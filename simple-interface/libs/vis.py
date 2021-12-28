import plotly.express as px
import plotly as plt
import plotly.graph_objects as go


def show_channels(timeseries, time):
    fig = plt.subplots.make_subplots(
        rows=timeseries.shape[0], 
        cols=1, 
        shared_xaxes=True
    )

    for i, series in enumerate(timeseries):
        fig.add_trace(
            go.Scatter(x=time, y=series),
            row=i + 1, col=1
        )
        
    return fig

def show_events(fig, events_df):
    for _, event in events_df.iterrows():
        fig.add_vrect(
            x0=event['start'], x1=event['end'],
            fillcolor='red', # TODO add second group 
            opacity=0.2,
            layer="below", 
            line_width=0,
            # annotation_text=event['type'], 
            # annotation_position="top left",
        )
    # fig.add_vline(x=131, line_width=3)

def show_slider(fig):
    fig.update_layout(
        legend_orientation="h", 
        xaxis3_rangeslider_visible=True, 
        xaxis3_rangeslider_thickness=0.1,
        height=500
    )


