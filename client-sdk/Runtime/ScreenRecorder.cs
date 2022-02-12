using UnityEngine;

using System;


namespace Emotions 
{
public class ScreenRecorder 
{
    private RenderTexture tempRenderTexture;
    private Texture2D tempTexture2D;

    public int screenWidth;
    public int screenHeight;
    public float period;

    private int resolutionMultiplier = 3;

    private byte[] lastFrame;

    public ScreenRecorder(
        int screenWidth, 
        int screenHeight, 
        float period
    ) 
    {
        this.screenWidth = screenWidth / resolutionMultiplier;
        this.screenHeight = screenHeight / resolutionMultiplier;
        this.period = period;

        tempRenderTexture = new RenderTexture(this.screenWidth, this.screenHeight, 0);
        tempTexture2D = new Texture2D(this.screenWidth, this.screenHeight, TextureFormat.RGBA32, false);
    }
    
    public void SaveFrame(RenderTexture source)
    {
        // TODO resize check

        Graphics.Blit (source, tempRenderTexture);
        
        RenderTexture.active = tempRenderTexture;
        tempTexture2D.ReadPixels(
            new Rect(0, 0, this.screenWidth, this.screenHeight), 
            0, 0
        );
        RenderTexture.active = null;

        lastFrame = tempTexture2D.GetRawTextureData();
    }    

    public VideoFrame GetData() 
    {
        var frame = new VideoFrame();
        frame.videoFrameBase64 = Convert.ToBase64String(lastFrame);
        frame.screenWidth = this.screenWidth;
        frame.screenHeight = this.screenHeight;
        frame.period = this.period;

        return frame;
    }
}
}