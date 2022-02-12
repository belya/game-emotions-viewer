using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;

using Newtonsoft.Json;

// TODO use properties instead of public fields

namespace Emotions 
{
    [Serializable]
    public class BoardFrame
    {
        public int channelsShape;
        public string device;
        public float[] boardData;
    }

    [Serializable]
    public class VideoFrame
    {
        public int screenWidth;
        public int screenHeight;
        public float period;

        public string videoFrameBase64;
    }

    [Serializable]
    public class FrameMessage
    {
        public float time;

        public VideoFrame screenVideoFrame;
        public VideoFrame webCamFrame;
        public BoardFrame boardFrame;
    }

    [Serializable]
    public class EventMessage
    {
        public float time;
        public string type;
    }
}