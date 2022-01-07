using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Threading;

using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;

namespace Emotions 
{
[Serializable]
class SignalFrame
{
    public float time;

    public int screenWidth;
    public int screenHeight;
    public float period;

    public int channelsShape;
    public string device;

    public float[] boardData;
    public string videoFrame;
}

[Serializable]
class SignalEvent
{
    public float time;
    public string type;
}

[RequireComponent(typeof(Camera))]
public class EmotionsSDK : MonoBehaviour 
{
    private Thread mqttThread;

    private Queue<SignalFrame> frameQueue;
    private MqttClient mqttClient;
    private BoardRecorder boardRecorder;
    private ScreenRecorder screenRecorder;

    private bool threadIsProcessing;
    private bool terminateThreadWhenDone;
    
    private float lastFrameTime;
    private float minPeriod = 0.05f;
    
    void Start () 
    {
        var screenWidth = GetComponent<Camera>().pixelWidth;
        var screenHeight = GetComponent<Camera>().pixelHeight;

        frameQueue = new Queue<SignalFrame>();
        boardRecorder = new BoardRecorder();
        screenRecorder = new ScreenRecorder(screenWidth, screenHeight);

        mqttClient = new MqttClient("localhost"); 
        var clientId = Guid.NewGuid().ToString();
        mqttClient.Connect(clientId); 

        if (mqttThread != null && (threadIsProcessing || mqttThread.IsAlive)) {
            threadIsProcessing = false;
            mqttThread.Join();
        }

        threadIsProcessing = true;
        mqttThread = new Thread(SendMessages);
        mqttThread.Start();
    }

    void OnRenderImage(RenderTexture source, RenderTexture destination)
    {
        screenRecorder.SaveFrame(source);
        Graphics.Blit(source, destination);
    }    

    void FixedUpdate()
    {
        var difference = Time.time - lastFrameTime;

        if (difference < minPeriod) {
            return; 
        }

        lastFrameTime = Time.time;

        var signalFrame = new SignalFrame();

        signalFrame.time = lastFrameTime;

        var videoFrame = screenRecorder.GetData();
        signalFrame.videoFrame = Convert.ToBase64String(videoFrame);
        signalFrame.screenWidth = screenRecorder.screenWidth;
        signalFrame.screenHeight = screenRecorder.screenHeight;
        signalFrame.period = minPeriod;

        var boardData = boardRecorder.GetData();
        signalFrame.boardData = boardData;
        signalFrame.channelsShape = boardRecorder.channels;
        signalFrame.device = boardRecorder.device;

        frameQueue.Enqueue(signalFrame);
    }
    
    void OnDisable() 
    {
        terminateThreadWhenDone = true;
        boardRecorder.Finalize();
    }

    private void SendMessage() {
        var signalFrame = frameQueue.Dequeue();
        var signalFrameJson = JsonUtility.ToJson(signalFrame);
        byte[] signalFrameBytes = System.Text.Encoding.ASCII.GetBytes(signalFrameJson);

        mqttClient.Publish(
            "/signal/frames", 
            signalFrameBytes, 
            MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, 
            false
        ); 
    }

    public void SendEvent(string eventType) {
        var signalEvent = new SignalEvent();
        signalEvent.time = Time.time;
        signalEvent.type = eventType;

        var signalEventJson = JsonUtility.ToJson(signalEvent);
        byte[] signalEventBytes = System.Text.Encoding.ASCII.GetBytes(signalEventJson);

        mqttClient.Publish(
            "/signal/events", 
            signalEventBytes, 
            MqttMsgBase.QOS_LEVEL_EXACTLY_ONCE, 
            false
        ); 
    }
    
    void SendMessages()
    {
        print ("EMOTIONS MQTT THREAD STARTED");

        while (threadIsProcessing) 
        {
            if(frameQueue.Count > 0)
            {
                SendMessage();

            }
            else
            {
                if(terminateThreadWhenDone)
                {
                    break;
                }

                Thread.Sleep(1);
            }
        }

        terminateThreadWhenDone = false;
        threadIsProcessing = false;

        print ("EMOTIONS MQTT THREAD STOPPED");
    }
}
}