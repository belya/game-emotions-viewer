using UnityEngine;

using brainflow;
using brainflow.math;

namespace Emotions 
{
class BoardRecorder
{
    private BoardShim board_shim = null;

    public float period;
    public int sampling_rate = 0;
    public string device = "OpenBCI8";

    public int channels = 0;

    private BoardShim InitializePlaybackBaord() {
        BrainFlowInputParams input_params = new BrainFlowInputParams();
        input_params.file = "/tmp/brainflow_data_test.csv";
        input_params.other_info = ((int)BoardIds.GANGLION_BOARD).ToString();
        Debug.Log(input_params);

        int board_id = (int)BoardIds.PLAYBACK_FILE_BOARD;
        board_shim = new BoardShim(board_id, input_params);

        return board_shim;
    }

    private BoardShim InitializeCytonBoard() {
        BrainFlowInputParams input_params = new BrainFlowInputParams();
        input_params.serial_port = "/dev/ttyUSB0";

        int board_id = (int)BoardIds.CYTON_BOARD;
        board_shim = new BoardShim(board_id, input_params);

        return board_shim;
    }

    // Start is called before the first frame update
    public BoardRecorder(float period)
    {
        this.period = period;
        try
        {
            BoardShim.set_log_file("/tmp/brainflow_log.txt");
            BoardShim.enable_dev_board_logger();

            board_shim = InitializePlaybackBaord();

            board_shim.prepare_session();
            board_shim.start_stream(450000, "file:///tmp/brainflow_stream.csv:w");

            sampling_rate = BoardShim.get_sampling_rate((int)BoardIds.CYTON_BOARD);
            Debug.Log("Brainflow streaming was started");
        }
        catch (BrainFlowException e)
        {
            Debug.Log(e);
        }
    }

    // Update is called once per frame
    public BoardFrame GetData()
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

        var frame = new BoardFrame();

        frame.boardData = data;
        frame.channelsShape = this.channels;
        frame.device = this.device;
        frame.period = this.period;

        return frame;
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
}