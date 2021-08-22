LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)
LOCAL_MODULE := sqlite3_static
LOCAL_SRC_FILES := libs/$(TARGET_ARCH_ABI)/libsqlite3.a
LOCAL_EXPORT_C_INCLUDES := $(LOCAL_PATH)/include
include $(PREBUILT_STATIC_LIBRARY)
