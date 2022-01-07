using UnityEngine;

using brainflow;
using brainflow.math;

namespace Emotions 
{
class BoardRecorder
{
    private BoardShim board_shim = null;
    public int sampling_rate = 0;
    public string device = "OpenBCI8";

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
}