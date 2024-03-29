TOP_PATH := $(call my-dir)/..

include $(CLEAR_VARS)
LOCAL_PATH := $(TOP_PATH)
LOCAL_SRC_FILES := sqlite3.c
LOCAL_MODULE := sqlite3_static
LOCAL_MODULE_FILENAME := libsqlite3
LOCAL_CFLAGS := \
  -DSQLITE_BYTEORDER=1234 \
  -DSQLITE_DIRECT_OVERFLOW_READ \
  -DSQLITE_ENABLE_ATOMIC_WRITE \
  -DSQLITE_ENABLE_BATCH_ATOMIC_WRITE \
  -DSQLITE_ENABLE_FTS4 \
  -DSQLITE_ENABLE_FTS5 \
  -D_FILE_OFFSET_BITS=64
include $(BUILD_STATIC_LIBRARY)
