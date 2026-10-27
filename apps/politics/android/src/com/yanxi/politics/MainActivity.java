package com.yanxi.politics;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.content.Intent;
import android.content.ActivityNotFoundException;
import android.net.Uri;
import android.graphics.Color;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.*;
import android.widget.FrameLayout;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONObject;

public final class MainActivity extends Activity {
    private static final String HOST="appassets.androidplatform.net";
    private static final int REQUEST_EXPORT_BACKUP=7101, REQUEST_IMPORT_BACKUP=7102;
    private WebView web;
    private StudyBridge bridge;
    private String backupToWrite;
    private final Map<String,String> assets=new HashMap<>();
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        assets.put("/index.html","text/html"); assets.put("/style.css","text/css");
        assets.put("/app.js","application/javascript"); assets.put("/questions.js","application/javascript");
        assets.put("/design.js","application/javascript"); assets.put("/design.css","text/css");
        FrameLayout root=new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(244,246,247));
        root.setOnApplyWindowInsetsListener((view,insets)->{
            if(Build.VERSION.SDK_INT>=30){android.graphics.Insets i=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());view.setPadding(i.left,i.top,i.right,i.bottom);}
            else{view.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());}
            return insets;
        });
        if(Build.VERSION.SDK_INT>=30){getWindow().setDecorFitsSystemWindows(false);}
        else getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR|View.SYSTEM_UI_FLAG_LAYOUT_STABLE|View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN|View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION);
        web=new WebView(this);
        web.setBackgroundColor(Color.rgb(244,246,247));
        bridge=new StudyBridge(this,web);
        web.addJavascriptInterface(bridge,"AndroidApp");
        WebSettings s=web.getSettings();
        s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setSupportMultipleWindows(false);s.setJavaScriptCanOpenWindowsAutomatically(false);
        web.setWebViewClient(new WebViewClient(){
            @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){
                Uri u=r.getUrl();String path=u.getPath();String type=assets.get(path);
                boolean image=path!=null&&path.matches("/images/[a-zA-Z0-9._-]+\\.webp");
                if("https".equals(u.getScheme())&&HOST.equals(u.getHost())&&(type!=null||image)){
                    if(image)type="image/webp";
                    try{return new WebResourceResponse(type,image?null:"UTF-8",getAssets().open(path.substring(1)));}catch(IOException ignored){}
                }
                return new WebResourceResponse("text/plain","UTF-8",404,"Not Found",new HashMap<>(),new ByteArrayInputStream(new byte[0]));
            }
            @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){
                Uri u=r.getUrl();if("https".equals(u.getScheme())&&HOST.equals(u.getHost()))return false;
                if(r.isForMainFrame()&&"https".equals(u.getScheme())){
                    try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(ActivityNotFoundException e){Toast.makeText(MainActivity.this,"未找到浏览器",Toast.LENGTH_SHORT).show();}
                }return true;
            }
        });
        root.addView(web,new FrameLayout.LayoutParams(-1,-1));setContentView(root);
        // The decor view and its insets controller may not exist before attachment.
        root.addOnAttachStateChangeListener(new View.OnAttachStateChangeListener() {
            @Override public void onViewAttachedToWindow(View view) {
                applySystemBarAppearance();
                view.requestApplyInsets();
            }
            @Override public void onViewDetachedFromWindow(View view) {}
        });
        if(root.isAttachedToWindow()) {
            applySystemBarAppearance();
            root.requestApplyInsets();
        }
        web.loadUrl("https://"+HOST+"/index.html");
        if(Build.VERSION.SDK_INT>=33)getOnBackInvokedDispatcher().registerOnBackInvokedCallback(0,()->handleBack());
    }
    private void applySystemBarAppearance() {
        if(Build.VERSION.SDK_INT>=30) {
            WindowInsetsController controller=getWindow().getInsetsController();
            if(controller!=null) {
                int appearance=WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS
                    |WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS;
                controller.setSystemBarsAppearance(appearance,appearance);
            }
        }
    }
    private void handleBack(){web.evaluateJavascript("typeof handleAndroidBack==='function'&&handleAndroidBack()",value->{if(!"true".equals(value))finish();});}
    public void exportBackupFile(String json){
        if(json==null||json.length()>5000000){Toast.makeText(this,"备份文件过大",Toast.LENGTH_SHORT).show();return;}
        backupToWrite=json;
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("application/json");
        intent.putExtra(Intent.EXTRA_TITLE,"研习政治-学习记录.json");
        try{startActivityForResult(intent,REQUEST_EXPORT_BACKUP);}
        catch(Exception e){backupToWrite=null;Toast.makeText(this,"无法打开文件保存窗口",Toast.LENGTH_SHORT).show();}
    }
    public void importBackupFile(){
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("application/json");
        try{startActivityForResult(intent,REQUEST_IMPORT_BACKUP);}
        catch(Exception e){Toast.makeText(this,"无法打开文件选择窗口",Toast.LENGTH_SHORT).show();}
    }
    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(resultCode!=RESULT_OK||data==null||data.getData()==null){backupToWrite=null;return;}
        if(requestCode==REQUEST_EXPORT_BACKUP){
            String json=backupToWrite;backupToWrite=null;
            if(json==null)return;
            try(OutputStream out=getContentResolver().openOutputStream(data.getData())){
                if(out==null)throw new IOException("No output stream");
                out.write(json.getBytes(StandardCharsets.UTF_8));out.flush();
                Toast.makeText(this,"学习记录已导出",Toast.LENGTH_SHORT).show();
            }catch(Exception e){Toast.makeText(this,"导出失败，请重试",Toast.LENGTH_LONG).show();}
        }else if(requestCode==REQUEST_IMPORT_BACKUP){
            try(InputStream in=getContentResolver().openInputStream(data.getData());ByteArrayOutputStream out=new ByteArrayOutputStream()){
                if(in==null)throw new IOException("No input stream");
                byte[] buffer=new byte[8192];int n;
                while((n=in.read(buffer))!=-1){if(out.size()+n>5000000)throw new IOException("Backup too large");out.write(buffer,0,n);}
                String json=new String(out.toByteArray(),StandardCharsets.UTF_8);
                if(web!=null)web.evaluateJavascript("window.onBackupImported&&window.onBackupImported("+JSONObject.quote(json)+")",null);
            }catch(Exception e){Toast.makeText(this,"备份文件无法读取",Toast.LENGTH_LONG).show();}
        }
    }
    @Override public void onBackPressed(){handleBack();}
    @Override protected void onPause(){super.onPause();if(web!=null)web.onPause();}
    @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
    @Override protected void onDestroy(){if(bridge!=null)bridge.destroy();if(web!=null)web.destroy();super.onDestroy();}
}
