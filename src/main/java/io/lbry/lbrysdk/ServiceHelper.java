package io.lbry.lbrysdk;

import android.content.Intent;
import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.content.SharedPreferences;
import android.os.AsyncTask;

import java.io.Closeable;
import java.io.File;
import java.io.InputStream;
import java.io.FileOutputStream;
import java.io.IOException;

public final class ServiceHelper {

    public static Intent buildIntent(Context ctx, String pythonServiceArgument, Class serviceClass, String pythonName) {
        Intent intent = new Intent(ctx, serviceClass);
        String argument = ctx.getFilesDir().getAbsolutePath() + "/app";
        intent.putExtra("androidPrivate", ctx.getFilesDir().getAbsolutePath());
        intent.putExtra("androidArgument", argument);
        intent.putExtra("serviceEntrypoint", "./" + pythonName + ".py");
        intent.putExtra("pythonName", pythonName);
        intent.putExtra("pythonHome", argument);
        intent.putExtra("pythonPath", argument + ":" + argument + "/lib");
        intent.putExtra("pythonServiceArgument", pythonServiceArgument);

        return intent;
    }

    public static void start(final Context ctx, String pythonServiceArgument, Class serviceClass, String pythonName) {
        Intent intent = buildIntent(ctx, pythonServiceArgument, serviceClass, pythonName);
        ctx.startService(intent);
    }

    public static void stop(Context ctx, Class serviceClass) {
        Intent intent = new Intent(ctx, serviceClass);
        ctx.stopService(intent);
    }

    private static void closeStream(Closeable closeable) {
        try {
            if (closeable != null) {
                closeable.close();
            }
        } catch (IOException ex) {
            // pass
        }
    }
}