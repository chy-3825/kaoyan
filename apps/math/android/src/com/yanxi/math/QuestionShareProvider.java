package com.yanxi.math;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.database.Cursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import java.io.File;
import java.io.FileNotFoundException;

/** Serves only the current cached question image to apps selected in Android's share sheet. */
public final class QuestionShareProvider extends ContentProvider {
    @Override public boolean onCreate(){return true;}
    @Override public String getType(Uri uri){
        String path=uri==null?"":uri.getLastPathSegment();
        if(path!=null&&path.endsWith(".png"))return "image/png";
        if(path!=null&&path.endsWith(".jpg"))return "image/jpeg";
        return "image/webp";
    }
    @Override public ParcelFileDescriptor openFile(Uri uri,String mode)throws FileNotFoundException{
        String name=uri==null?"":uri.getLastPathSegment();
        if(name==null||!name.matches("q-[A-Za-z0-9_-]{1,120}\\.(webp|png|jpg)")||!"r".equals(mode))
            throw new FileNotFoundException("Unsupported question image");
        File root=new File(getContext().getCacheDir(),"question-share");
        File file=new File(root,name);
        // The accepted filename cannot contain path separators or dot segments.
        if(!file.isFile())throw new FileNotFoundException("Question image is unavailable");
        return ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
    }
    @Override public Cursor query(Uri uri,String[] projection,String selection,String[] selectionArgs,String sortOrder){return null;}
    @Override public Uri insert(Uri uri,ContentValues values){return null;}
    @Override public int delete(Uri uri,String selection,String[] selectionArgs){return 0;}
    @Override public int update(Uri uri,ContentValues values,String selection,String[] selectionArgs){return 0;}
}
