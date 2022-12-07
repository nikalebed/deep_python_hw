import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from urllib.request import urlopen
import json

df = pd.read_csv('crimedata.csv')

states = st.sidebar.multiselect(
    'Select states',
    df['state'].unique(), ['CA', 'NY'])
population = st.sidebar.slider(
    'Select population range',
    int(df['population'].min()), int(df['population'].max()), ()
)
apply = st.sidebar.checkbox('Apply filters')

if apply:
    df_filter = df[
        (df['state'].isin(states)) & (population[0] <= df['population']) & (
                df['population'] <= population[1])]
else:
    df_filter = df
########################################################################

st.title('Crime in US states')
total_name = df.loc[:, 'murders':'arsons':2].columns
rel_name = df.loc[:, 'murdPerPop':'arsonsPerPop':2].columns

crime_name_dict = {
    'total': {total_name[i]: total_name[i] for i in range(len(total_name))},
    'per population': {total_name[i]: rel_name[i] for i in
                       range(len(total_name))}
}

crime = st.selectbox('Select crime type',
                     df.loc[:, 'murders':'arsons':2].columns)

total = st.radio(label='crime number',
                 options=['total', 'per population'],
                 horizontal=True)

data = df.groupby('state').agg('sum').loc[:,
       'murders':'arsons':].reset_index()

fig = px.choropleth(data, locationmode="USA-states", locations='state',
                    color=crime_name_dict[total][crime],
                    color_continuous_scale="Viridis",
                    range_color=(0, data[crime_name_dict[total][crime]].std()),
                    scope="usa",
                    hover_data=["state", crime_name_dict[total][crime]]
                    )
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig)

########################################################################
st.title('Crime types share')
st.write('filters can be applied')
data = df_filter.agg(['sum']).loc[:,
       'murders':'arsons':2].agg(['sum']).T.reset_index()
fig = px.pie(data, values='sum', names='index')
st.plotly_chart(fig)
########################################################################
st.title('Crime numbers by median income')

income = st.slider(
    'Select income range', min(df_filter['medIncome']) - 1,
                           max(df_filter['medIncome']) + 1, ()
)
data = df_filter[(income[0] <= df_filter.medIncome) & (
        df_filter['medIncome'] <= income[1])].loc[:,
       'murders':'arsons':2].agg(['sum']).T.reset_index()
fig = px.bar(data, x='index', y='sum')
st.plotly_chart(fig)
########################################################################
st.title('Violent crime and police relation')
fig = px.scatter(df_filter, x="PolicPerPop", y="ViolentCrimesPerPop",
                 size="LandArea", color="state",
                 log_x=True, size_max=60)
st.plotly_chart(fig)

########################################################################
st.title('Relationship between unemployment and crime')
fig = px.scatter(df_filter, x='PctUnemployed', y='burglPerPop',
                 trendline="ols")
st.plotly_chart(fig)

snow = st.checkbox('let it snow?')
if snow:
    st.snow()
