import wget
import pandas as pd
import numpy as np
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
from os.path import exists

#  # Get the data
if not exists('./data/spacex_launch_dash.csv'):
    url = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_dash.csv'
    wget.download(url, './data/')

df = pd.read_csv('./data/spacex_launch_dash.csv')
max_payload = df['Payload Mass (kg)'].max()
min_payload = df['Payload Mass (kg)'].min()

#  # Create the app and its layout
app = dash.Dash(__name__)
app.layout = html.Div(
    children=[
        html.H1('SpaceX Launch Records Dashboard',
                style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40,
                       'padding-bottom': '25px', 'border-bottom': '4px solid #ccc'}),
        html.Div(
            dcc.Dropdown(
                id='site-dropdown',
                options=[{'label': i, 'value': i} for i in set(df['Launch Site'])] + [
                    {'label': 'All Sites', 'value': 'ALL'}],
                value='ALL',
                searchable=True,
                style={'height': '30px', 'font-size': '20px'}),
            style={'width': '50%', 'margin': '0 auto', 'border-bottom': '4px solid #999'}
        ),
        html.Br(),
        html.Div([], id='pie-chart', style={'width': '50%', 'margin': '0 auto', 'min-width': '600px'}),
        html.Br(),
        html.H3('Select Payload Range (kg)'),
        html.Div(
            dcc.RangeSlider(
                id='payload-slider',
                min=min_payload, max=max_payload,
                step=1000,
                value=[min_payload, max_payload],
                marks={i: str(i) for i in range(1000, 10000, 1000)} | {9600: '9600'}
            ),
            style={'width': '70%', 'margin': '0 auto'}),
        html.Div([], id='scatter-chart'),
    ],
    style={'text-align': 'center', 'width': '1200px', 'margin': '0 auto',
           'border': '4px solid #ccc', 'border-radius': '10px', 'font-family': 'arial, sans-serif'})


#  # The callback decorator
@app.callback(
    [Output('pie-chart', component_property='children'),
     Output('scatter-chart', component_property='children')],
    [Input('site-dropdown', component_property='value'),
     Input('payload-slider', component_property='value')],
    [State('pie-chart', 'children'),
     State('scatter-chart', 'children')])
def get_pie_plot(site, payload_range, c1, c2):
    site = site.strip()
    p_df = df[(df['Payload Mass (kg)'] >= payload_range[0]) & (df['Payload Mass (kg)'] <= payload_range[1])]

    if site == 'ALL':
        # pie plot
        pie_plot = px.pie(df, values='class', names='Launch Site', title='Pie Chart of Success Rate by Launch Site')

        # scatter plot, add jitter
        p_df['class'] = p_df['class'] + np.random.normal(0, 2, p_df.shape[0]) * 0.015
        scatter_plot = px.strip(p_df, x='Payload Mass (kg)', y='class', color='Booster Version Category',
                                title='Plot of Flight Outcomes for Payload Mass in the Selected Range',
                                stripmode='group', orientation='v')
        scatter_plot.update_yaxes(title=None, tickvals=[0, 1], ticktext=['Failure', 'Success'])
    else:
        site_df = df[df['Launch Site'] == site]
        site_df['outcome'] = site_df['class'].map(lambda x: 'Success' if x == 1 else 'Failure')

        # pie plot
        pie_df = site_df['outcome'].value_counts()
        pie_plot = px.pie(pie_df, values='outcome', names=pie_df.keys(), color=pie_df.keys(),
                          color_discrete_map={'Success': 'rgb(99, 110, 250)', 'Failure': 'rgb(239, 85, 59)'},
                          title='Pie chart of success/failure rates at Launch Site "' + site + '"')

        # scatter: Add a bit of jitter so we can see all points
        p_df = site_df[
            (site_df['Payload Mass (kg)'] >= payload_range[0]) & (site_df['Payload Mass (kg)'] <= payload_range[1])]
        p_df['class'] = p_df['class'] + np.random.normal(0, 2, p_df.shape[0]) * 0.015
        scatter_plot = px.scatter(p_df, x='Payload Mass (kg)', y='class', color='Booster Version Category',
                                  title='Plot of Flight Outcome for Payload Mass in the Selected Range at Launch Site ' + site)
        scatter_plot.update_yaxes(title=None, tickvals=[0, 1], ticktext=['Failure', 'Success'])

    pie_plot.update_layout(title_x=0.5)
    scatter_plot.update_layout(plot_bgcolor='#def', title_x=0.5)
    return [dcc.Graph(figure=pie_plot), dcc.Graph(figure=scatter_plot)]


#  # Run the app
if __name__ == '__main__':
    app.run_server()
