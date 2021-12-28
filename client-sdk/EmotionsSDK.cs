using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Threading;

using brainflow;
using brainflow.math;

using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;

[Serializable]
public class SignalFrame
{
    public float time;

    public int screenWidth;
    public int screenHeight;
    public float period;

    public int channels;
    public int samplingRate;

    public float[] boardData;
    public byte[] videoFrame;
}

[Serializable]
public class SignalEvent
{
    public float time;
    public string type;
}

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

public class BoardRecorder
{
    private BoardShim board_shim = null;
    public int sampling_rate = 0;

    public int channels = 0;

    // Start is called before the first frame update
    public BoardRecorder()
    {
        try
        {
            BoardShim.set_log_file("brainflow_log.txt");
            BoardShim.enable_dev_board_logger();

            BrainFlowInputParams input_params = new BrainFlowInputParams();
            int board_id = (int)BoardIds.SYNTHETIC_BOARD;
            board_shim = new BoardShim(board_id, input_params);
            board_shim.prepare_session();
            board_shim.start_stream(450000, "file://brainflow_data.csv:w");
            sampling_rate = BoardShim.get_sampling_rate(board_id);
            Debug.Log("Brainflow streaming was started");
        }
        catch (BrainFlowException e)
        {
            Debug.Log(e);
        }
    }

    // Update is called once per frame
    public float[] GetData()
    {
        if (board_shim == null)
        {
            return null;
        };

        int number_of_data_points = sampling_rate;
        double[,] doubleData = board_shim.get_board_data(number_of_data_points);

        float[] data = new float[
            doubleData.GetLength(0) * doubleData.GetLength(1)
        ];

        channels = doubleData.GetLength(0);

        for (var i = 0; i < doubleData.GetLength(0); i++) {
            for (var j = 0; j < doubleData.GetLength(1); j++) 
                data[i * doubleData.GetLength(1) + j] = (float) doubleData[i, j];
        }

        return data;
    }

    // you need to call release_session and ensure that all resources correctly released
    public void Finalize()
    {
        if (board_shim != null)
        {
            try
            {
                board_shim.release_session();
            }
            catch (BrainFlowException e)
            {
                Debug.Log(e);
            }
            Debug.Log("Brainflow streaming was stopped");
        }
    }
}


[RequireComponent(typeof(Camera))]
public class NewTestScript : MonoBehaviour 
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
        signalFrame.videoFrame = videoFrame;
        signalFrame.screenWidth = screenRecorder.screenWidth;
        signalFrame.screenHeight = screenRecorder.screenHeight;
        signalFrame.period = minPeriod;

        var boardData = boardRecorder.GetData();
        signalFrame.boardData = boardData;
        signalFrame.channels = boardRecorder.channels;
        signalFrame.samplingRate = boardRecorder.sampling_rate;

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
