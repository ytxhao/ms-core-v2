package com.msl.application;

import androidx.appcompat.app.AppCompatActivity;

import android.annotation.TargetApi;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;


import com.google.android.material.snackbar.Snackbar;
import com.msl.app.MSLLog;
import com.msl.application.databinding.ActivityMainBinding;

import java.util.ArrayList;

public class MainActivity extends AppCompatActivity {

//    static {
//        System.loadLibrary("msl-core-jni");
//    }
    private static final String TAG = "MainActivity";
    private static final int PERMISSION_REQUEST = 2;
    private ActivityMainBinding binding;
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());
        requestPermissions();
        binding.btnTest.setOnClickListener(view -> {
            MSLLog.nativeTracker(TAG,"onClick test btn");
        });
    }

    @TargetApi(Build.VERSION_CODES.M)
    private void requestPermissions() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) {
            return;
        }

        String[] missingPermissions = getMissingPermissions();
        if (missingPermissions.length != 0) {
            Snackbar.make(binding.getRoot(), "请申请权限", Snackbar.LENGTH_INDEFINITE).
                    setAction("授权", view -> requestPermissions(missingPermissions, PERMISSION_REQUEST)).show();
        }
    }

    @TargetApi(Build.VERSION_CODES.M)
    private String[] getMissingPermissions() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) {
            return new String[0];
        }

        PackageInfo info;
        try {
            info = getPackageManager().getPackageInfo(getPackageName(), PackageManager.GET_PERMISSIONS);
        } catch (PackageManager.NameNotFoundException e) {
            Log.w(TAG, "Failed to retrieve permissions.");
            return new String[0];
        }

        if (info.requestedPermissions == null) {
            Log.w(TAG, "No requested permissions.");
            return new String[0];
        }

        ArrayList<String> missingPermissions = new ArrayList<>();
        for (int i = 0; i < info.requestedPermissions.length; i++) {
            if ((info.requestedPermissionsFlags[i] & PackageInfo.REQUESTED_PERMISSION_GRANTED) == 0) {
                missingPermissions.add(info.requestedPermissions[i]);
            }
        }
        Log.d(TAG, "Missing permissions: " + missingPermissions);

        return missingPermissions.toArray(new String[0]);
    }
}