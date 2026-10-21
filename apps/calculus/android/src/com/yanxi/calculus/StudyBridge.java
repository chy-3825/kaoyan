package com.yanxi.calculus;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.text.InputType;
import android.util.Base64;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.concurrent.*;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

public final class StudyBridge {
    private static final String KEY_ALIAS="yanxi-calculus-deepseek-key";
    private static final String DEFAULT_MODEL="deepseek-flash";
    private final Activity activity;
    private final WebView web;
    private final SharedPreferences prefs;
    private final ExecutorService executor=Executors.newFixedThreadPool(2);
    private final Semaphore slots=new Semaphore(2);
    private volatile boolean destroyed;
    public StudyBridge(Activity a,WebView w){activity=a;web=w;prefs=a.getSharedPreferences("math-deepseek",Context.MODE_PRIVATE);}
    private SecretKey encryptionKey() throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);
        if(store.containsAlias(KEY_ALIAS))return (SecretKey)store.getKey(KEY_ALIAS,null);
        KeyGenerator generator=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(KEY_ALIAS,KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return generator.generateKey();
    }
    private synchronized String readKey() throws Exception {
        String encrypted=prefs.getString("key",null),iv=prefs.getString("iv",null);
        if(encrypted==null||iv==null)return "";
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,encryptionKey(),new GCMParameterSpec(128,Base64.decode(iv,Base64.NO_WRAP)));
        return new String(c.doFinal(Base64.decode(encrypted,Base64.NO_WRAP)),StandardCharsets.UTF_8);
    }
    private synchronized void storeKey(String key) throws Exception {
        Cipher c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,encryptionKey());
        if(!prefs.edit().putString("key",Base64.encodeToString(c.doFinal(key.getBytes(StandardCharsets.UTF_8)),Base64.NO_WRAP)).putString("iv",Base64.encodeToString(c.getIV(),Base64.NO_WRAP)).commit())throw new IOException("Cannot save key");
    }
    @JavascriptInterface public boolean hasApiKey(){try{return !readKey().isEmpty();}catch(Exception e){return false;}}
    @JavascriptInterface public boolean copyText(String text){
        if(text==null||text.length()>50000)return false;
        try{ClipboardManager clipboard=(ClipboardManager)activity.getSystemService(Context.CLIPBOARD_SERVICE);clipboard.setPrimaryClip(ClipData.newPlainText("考研高等数学题目",text));return true;}catch(Exception e){return false;}
    }
    @JavascriptInterface public void shareText(String text){
        if(text==null||text.length()>20000)return;
        activity.runOnUiThread(()->{
            if(destroyed)return;
            Intent send=new Intent(Intent.ACTION_SEND);send.setType("text/plain");
            send.putExtra(Intent.EXTRA_SUBJECT,"研习高数意见反馈");send.putExtra(Intent.EXTRA_TEXT,text);
            try{activity.startActivity(Intent.createChooser(send,"分享反馈"));}
            catch(Exception e){Toast.makeText(activity,"暂时无法打开分享面板",Toast.LENGTH_SHORT).show();}
        });
    }
    @JavascriptInterface public void exportBackup(String json){
        if(destroyed||json==null||json.length()>5000000)return;
        activity.runOnUiThread(()->{if(!destroyed&&activity instanceof MainActivity)((MainActivity)activity).exportBackupFile(json);});
    }
    @JavascriptInterface public void importBackup(){
        activity.runOnUiThread(()->{if(!destroyed&&activity instanceof MainActivity)((MainActivity)activity).importBackupFile();});
    }
    @JavascriptInterface public void configureApi(){activity.runOnUiThread(()->{
        if(destroyed)return;
        LinearLayout fields=new LinearLayout(activity);fields.setOrientation(LinearLayout.VERTICAL);int pad=(int)(24*activity.getResources().getDisplayMetrics().density);fields.setPadding(pad,pad/2,pad,pad/2);
        TextView label=new TextView(activity);label.setText(hasApiKey()?"API Key 已保存，留空则保留":"输入你自己的 DeepSeek API Key");fields.addView(label);
        EditText key=new EditText(activity);key.setHint("API Key");key.setSingleLine(true);key.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);fields.addView(key);
        TextView modelLabel=new TextView(activity);modelLabel.setText("模型名称");fields.addView(modelLabel);
        EditText model=new EditText(activity);model.setSingleLine(true);model.setText(prefs.getString("model",DEFAULT_MODEL));fields.addView(model);
        AlertDialog dialog=new AlertDialog.Builder(activity).setTitle("DeepSeek API 设置").setView(fields).setPositiveButton("保存",null).setNegativeButton("取消",null).setNeutralButton("删除密钥",(d,w)->{prefs.edit().remove("key").remove("iv").apply();Toast.makeText(activity,"密钥已删除",Toast.LENGTH_SHORT).show();}).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
            String k=key.getText().toString().trim(),m=model.getText().toString().trim();
            if(!m.matches("[a-zA-Z0-9._-]{1,80}")){model.setError("请输入有效模型名称");return;}
            if(k.isEmpty()&&!hasApiKey()){key.setError("请输入 API Key");return;}
            if(k.length()>4096||k.contains("\n")||k.contains("\r")){key.setError("API Key 格式不正确");return;}
            try{if(!k.isEmpty())storeKey(k);prefs.edit().putString("model",m).apply();key.setText("");dialog.dismiss();web.evaluateJavascript("window.onApiConfigured&&window.onApiConfigured()",null);}catch(Exception e){Toast.makeText(activity,"密钥保存失败，请重试",Toast.LENGTH_LONG).show();}
        }));dialog.show();
    });}
    @JavascriptInterface public void shareQuestionImage(String id,String details,String dataUrl){
        if(destroyed||id==null||!id.matches("[A-Za-z0-9_-]{1,120}")||dataUrl==null||dataUrl.length()>12000000)return;
        int comma=dataUrl.indexOf(',');
        if(comma<0||!dataUrl.startsWith("data:image/"))return;
        String mime=dataUrl.substring(5,comma).split(";",2)[0];
        String extension="image/png".equals(mime)?"png":"image/jpeg".equals(mime)?"jpg":"webp";
        try{
            byte[] bytes=Base64.decode(dataUrl.substring(comma+1),Base64.DEFAULT);
            if(bytes.length==0||bytes.length>8*1024*1024)return;
            File directory=new File(activity.getCacheDir(),"question-share");
            if(!directory.exists()&&!directory.mkdirs())throw new IOException("cache unavailable");
            try(FileOutputStream out=new FileOutputStream(new File(directory,"q-"+id+"."+extension))){out.write(bytes);out.flush();}
            Uri uri=Uri.parse("content://"+activity.getPackageName()+".share/q-"+id+"."+extension);
            activity.runOnUiThread(()->{
                if(destroyed)return;
                Intent send=new Intent(Intent.ACTION_SEND);send.setType("image/*");
                send.putExtra(Intent.EXTRA_STREAM,uri);send.putExtra(Intent.EXTRA_TEXT,details==null?"考研高等数学题目":details);
                send.setClipData(ClipData.newUri(activity.getContentResolver(),"考研高数原题图",uri));
                send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                try{activity.startActivity(Intent.createChooser(send,"分享原题图"));}
                catch(Exception e){Toast.makeText(activity,"暂时无法打开分享面板",Toast.LENGTH_SHORT).show();}
            });
        }catch(Exception e){activity.runOnUiThread(()->Toast.makeText(activity,"题目图分享失败，请重试",Toast.LENGTH_SHORT).show());}
    }
    @JavascriptInterface public void requestExplanation(String id,String prompt){
        if(destroyed||id==null||id.length()>150)return;
        if(prompt==null||prompt.isEmpty()||prompt.length()>30000){reply(id,null,"题目内容无效，请复制题目自行提问。");return;}
        if(!slots.tryAcquire()){reply(id,null,"已有解析正在生成，请稍后重试。");return;}
        executor.execute(()->{
            HttpURLConnection connection=null;
            try{
                String key=readKey();if(key.isEmpty()){reply(id,null,"请先设置 DeepSeek API Key。");return;}
                JSONObject body=new JSONObject().put("model",prefs.getString("model",DEFAULT_MODEL)).put("stream",false).put("max_tokens",4096);
                body.put("messages",new JSONArray().put(new JSONObject().put("role","user").put("content",prompt)));
                connection=(HttpURLConnection)new URL("https://api.deepseek.com/chat/completions").openConnection();
                connection.setInstanceFollowRedirects(false);connection.setRequestMethod("POST");connection.setConnectTimeout(15000);connection.setReadTimeout(75000);connection.setDoOutput(true);
                connection.setRequestProperty("Authorization","Bearer "+key);connection.setRequestProperty("Content-Type","application/json; charset=utf-8");
                byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);connection.setFixedLengthStreamingMode(data.length);
                try(OutputStream out=connection.getOutputStream()){out.write(data);}
                int code=connection.getResponseCode();
                if(code!=200){reply(id,null,errorForStatus(code));return;}
                ByteArrayOutputStream output=new ByteArrayOutputStream();
                try(InputStream input=connection.getInputStream()){byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1){if(output.size()+n>1024*1024)throw new IOException("Response too large");output.write(buffer,0,n);}}
                JSONObject response=new JSONObject(new String(output.toByteArray(),StandardCharsets.UTF_8));
                JSONObject choice=response.getJSONArray("choices").getJSONObject(0);
                String content=choice.getJSONObject("message").optString("content","");
                if(content.trim().isEmpty()||"null".equals(content)){reply(id,null,"接口未返回解析正文，请重试或更换模型。");return;}
                if("length".equals(choice.optString("finish_reason")))content+="\n\n（本次解析达到长度上限，内容可能未完整生成。）";
                reply(id,content,null);
            }catch(SocketTimeoutException e){reply(id,null,"请求超时，可稍后重试或复制题目自行提问。");}
            catch(Exception e){reply(id,null,"解析请求失败，请检查网络、API Key 和模型名称。也可复制题目自行提问。");}
            finally{if(connection!=null)connection.disconnect();slots.release();}
        });
    }
    @JavascriptInterface public void requestImageExplanation(String id,String prompt,String imageData){
        if(destroyed||id==null||id.length()>150)return;
        if(prompt==null||prompt.isEmpty()||prompt.length()>30000||imageData==null||imageData.length()>12000000||!imageData.matches("(?s)^data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=\\r\\n]+$")){
            reply(id,null,"题目图或题目说明无效，请重新进入题目后重试。");return;
        }
        if(!slots.tryAcquire()){reply(id,null,"已有解析正在生成，请稍后重试。");return;}
        executor.execute(()->{
            HttpURLConnection connection=null;
            try{
                String key=readKey();if(key.isEmpty()){reply(id,null,"请先设置 DeepSeek API Key。也可分享原题图到其他 AI。 ");return;}
                String mime=imageData.substring(5,imageData.indexOf(';'));
                JSONObject textPart=new JSONObject().put("type","text").put("text",prompt);
                JSONObject imageUrl=new JSONObject().put("url",imageData);
                JSONObject imagePart=new JSONObject().put("type","image_url").put("image_url",imageUrl);
                JSONArray content=new JSONArray().put(textPart).put(imagePart);
                JSONObject message=new JSONObject().put("role","user").put("content",content);
                JSONObject body=new JSONObject().put("model",prefs.getString("model",DEFAULT_MODEL)).put("stream",false).put("max_tokens",4096)
                    .put("messages",new JSONArray().put(message));
                connection=(HttpURLConnection)new URL("https://api.deepseek.com/chat/completions").openConnection();
                connection.setInstanceFollowRedirects(false);connection.setRequestMethod("POST");connection.setConnectTimeout(15000);connection.setReadTimeout(90000);connection.setDoOutput(true);
                connection.setRequestProperty("Authorization","Bearer "+key);connection.setRequestProperty("Content-Type","application/json; charset=utf-8");
                byte[] data=body.toString().getBytes(StandardCharsets.UTF_8);connection.setFixedLengthStreamingMode(data.length);
                try(OutputStream out=connection.getOutputStream()){out.write(data);}
                int code=connection.getResponseCode();
                if(code!=200){reply(id,null,errorForStatus(code));return;}
                ByteArrayOutputStream output=new ByteArrayOutputStream();
                try(InputStream input=connection.getInputStream()){byte[] buffer=new byte[8192];int n;while((n=input.read(buffer))!=-1){if(output.size()+n>1024*1024)throw new IOException("Response too large");output.write(buffer,0,n);}}
                JSONObject response=new JSONObject(new String(output.toByteArray(),StandardCharsets.UTF_8));
                JSONObject choice=response.getJSONArray("choices").getJSONObject(0);
                String contentText=choice.getJSONObject("message").optString("content","");
                if(contentText.trim().isEmpty()||"null".equals(contentText)){reply(id,null,"接口未返回解析正文，请重试或确认模型支持图片输入。");return;}
                if("length".equals(choice.optString("finish_reason")))contentText+="\n\n（本次解析达到长度上限，内容可能未完整生成。）";
                reply(id,contentText,null);
            }catch(SocketTimeoutException e){reply(id,null,"请求超时，可稍后重试或分享原题图自行提问。");}
            catch(Exception e){reply(id,null,"解析请求失败，请检查网络、API Key 和视觉模型名称。也可分享原题图自行提问。");}
            finally{if(connection!=null)connection.disconnect();slots.release();}
        });
    }
    static String errorForStatus(int code){
        switch(code){case 401:return "API Key 无效，请检查后重试。";case 402:return "API 账户余额不足，可分享原题图到其他 AI。";case 429:return "请求过于频繁，请稍后重试。";case 400:case 422:return "接口参数或模型不支持图片，请使用 deepseek-flash。";default:return "解析服务暂时不可用（HTTP "+code+"），可分享原题图自行提问。";}
    }
    private void reply(String id,String text,String error){
        try{JSONObject result=new JSONObject().put("id",id);if(error!=null)result.put("error",error);else result.put("text",text);
            activity.runOnUiThread(()->{if(!destroyed)web.evaluateJavascript("window.onNativeExplanation&&window.onNativeExplanation("+result.toString()+")",null);});
        }catch(Exception ignored){}
    }
    public void destroy(){destroyed=true;executor.shutdownNow();}
}
