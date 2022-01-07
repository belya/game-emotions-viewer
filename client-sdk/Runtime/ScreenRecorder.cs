using UnityEngine;

namespace Emotions 
{
public class ScreenRecorder 
{
    private RenderTexture tempRenderTexture;
    private Texture2D tempTexture2D;

    public int screenWidth;
    public int screenHeight;

    private byte[] lastFrame;

    public ScreenRecorder(int screenWidth, int screenHeight) 
    {
        this.screenWidth = screenWidth;
        this.screenHeight = screenHeight;

        tempRenderTexture = new RenderTexture(screenWidth, screenHeight, 0);
        tempTexture2D = new Texture2D(screenWidth, screenHeight, TextureFormat.RGB24, false);
    }
    
    public void SaveFrame(RenderTexture source)
    {
        // TODO resize check

        Graphics.Blit (source, tempRenderTexture);
        
        RenderTexture.active = tempRenderTexture;
        tempTexture2D.ReadPixels(new Rect(0, 0, Screen.width, Screen.height),0,0);
        RenderTexture.active = null;

        lastFrame = tempTexture2D.GetRawTextureData();
    }    

    public byte[] GetData() 
    {
        return lastFrame;
    }
}
}