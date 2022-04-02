#ifndef _AN_LOG_H_
#define _AN_LOG_H_

#include <android/log.h>

#ifdef AN_DEBUG
#define LOGD(TAG, ...) __android_log_print(ANDROID_LOG_DEBUG, TAG, __VA_ARGS__)
#define LOGE(TAG, ...) __android_log_print(ANDROID_LOG_ERROR, TAG, __VA_ARGS__)
#define LOGI(TAG, ...) __android_log_print(ANDROID_LOG_INFO, TAG, __VA_ARGS__)
#define LOGW(TAG, ...) __android_log_print(ANDROID_LOG_WARN, TAG, __VA_ARGS__)
#define LOGV(TAG, ...) __android_log_print(ANDROID_LOG_VERBOSE, TAG, __VA_ARGS__)

#else

#define LOGV(...)
#define LOGD(...)
#define LOGI(...)
#define LOGW(...)
#define LOGE(...)
#define LOGF(...)
#endif

#endif





