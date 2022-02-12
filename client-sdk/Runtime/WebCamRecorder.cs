using UnityEngine;

using System;

using System.Runtime.InteropServices;

namespace Emotions 
{
public class WebCamRecorder 
{
    private WebCamTexture webcam = null;
    private float period;
    private int resolutionMultiplier = 10 * 4;

    private static byte[] Color32ArrayToByteArray(Color32[] colors)
    {
        if (colors == null || colors.Length == 0)
            return null;

        int lengthOfColor32 = Marshal.SizeOf(typeof(Color32));
        int length = lengthOfColor32 * colors.Length;
        byte[] bytes = new byte[length];

        GCHandle handle = default(GCHandle);
        try
        {
            handle = GCHandle.Alloc(colors, GCHandleType.Pinned);
            IntPtr ptr = handle.AddrOfPinnedObject();
            Marshal.Copy(ptr, bytes, 0, length);
        }
        finally
        {
            if (handle != default(GCHandle))
                handle.Free();
        }

        return bytes;
    }

    public WebCamRecorder(float period) 
    {
        this.period = period;

        WebCamDevice[] devices = WebCamTexture.devices;
        this.webcam = new WebCamTexture(
            devices[0].name, 
            16 * resolutionMultiplier, 
            9 * resolutionMultiplier
        );

        webcam.Play();
    }
    
    public VideoFrame GetData() 
    {
        var image = new Color32[webcam.width * webcam.height];
        webcam.GetPixels32(image);
        var bytes = Color32ArrayToByteArray(image);

        var frame = new VideoFrame();
        frame.videoFrameBase64 = Convert.ToBase64String(bytes);
        frame.screenWidth = webcam.width;
        frame.screenHeight = webcam.height;
        frame.period = this.period;

        return frame;
    }
}
}