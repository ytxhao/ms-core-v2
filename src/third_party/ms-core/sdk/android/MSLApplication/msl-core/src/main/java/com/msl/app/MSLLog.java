package com.msl.app;

public class MSLLog {
    static {
        System.loadLibrary("msl-core-jni");
    }
    public static native void nativeTracker(String tag, String log);
}
