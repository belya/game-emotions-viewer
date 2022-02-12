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
[RequireComponent(typeof(Camera))]
public class EmotionsSDK : MonoBehaviour 
{
    private Thread mqttThread;

    private Queue<FrameMessage> frameQueue;
    private MqttClient mqttClient;

    private BoardRecorder boardRecorder;
    private ScreenRecorder screenRecorder;
    private WebCamRecorder webCamRecorder;

    private bool threadIsProcessing;
    private bool terminateThreadWhenDone;
    
    private float lastFrameTime;
    private float minPeriod = 0.05f;
    
    void Start () 
    {
        var cameraComponent = GetComponent<Camera>();
        var screenWidth = cameraComponent.pixelWidth;
        var screenHeight = cameraComponent.pixelHeight;

        frameQueue = new Queue<FrameMessage>();

        boardRecorder = new BoardRecorder(minPeriod);
        screenRecorder = new ScreenRecorder(screenWidth, screenHeight, minPeriod);
        webCamRecorder = new WebCamRecorder(minPeriod);

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

        var screenVideoFrame = screenRecorder.GetData();
        // var boardFrame = boardRecorder.GetData();
        var webCamFrame = webCamRecorder.GetData();
        
        var signalFrame = new FrameMessage();
        signalFrame.time = lastFrameTime;
        signalFrame.screenVideoFrame = screenVideoFrame;
        signalFrame.webCamFrame = webCamFrame;
        // signalFrame.boardFrame = boardFrame;

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
        var signalEvent = new EventMessage();
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