#include <jni.h>
#include <string>
#include <test.h>
#include "an_log.h"
#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT void JNICALL
Java_com_msl_app_MSLLog_nativeTracker(JNIEnv* env, jclass clazz, jstring tag, jstring log) {
    std::string hello = "Hello from C++qfdsafw";
    int a = test(2,5);
    LOGD("yjy","a:%d",a);
    env->NewStringUTF(hello.c_str());
}

#ifdef __cplusplus
}
#endif