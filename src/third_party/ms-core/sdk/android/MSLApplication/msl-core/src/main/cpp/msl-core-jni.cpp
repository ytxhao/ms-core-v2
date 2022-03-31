#include <jni.h>
#include <string>

#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT void JNICALL
Java_com_msl_app_MSLLog_nativeTracker(JNIEnv* env, jclass clazz, jstring tag, jstring log) {
    std::string hello = "Hello from C++";
    env->NewStringUTF(hello.c_str());
}

#ifdef __cplusplus
}
#endif