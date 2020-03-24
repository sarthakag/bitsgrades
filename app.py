import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import random
import pandas as pd
import numpy as np
import base64
import io
import webbrowser
import time
from flask import Flask
from pyfladesk import init_gui

grades = ['A','A-','B','B-','C','C-','D','D-','E']
marks={'A': 10,'A-': 9,'B': 8,'B-': 7,'C': 6,'C-': 5,'D': 4,'D-': 3,'E': 2}

def input_field( grade ):
    return html.Div(
        children = [
            # html.Label( children = grade, style = { 'width' : '30%', 'display' : "table-cell" } ),
            dcc.Input( id = grade, type = 'number', size = '3',style = { 'display' : "None" } ),
        ],
        style = { 'display' : 'table' },
        className="three columns",
    )

def graph( inp , cur_inp ):

	inp.dropna(subset=['Name', 'MARKS'],inplace=True)
	# print(inp)
	inp['MARKS'] = pd.Series([ int(i) for i in inp['MARKS'] ] )
	traces=[]
	MGPA=[]
	count = inp.groupby('MARKS').count().max()[0]

	inp.sort_values(['MARKS'],inplace=True)

	txt = pd.DataFrame(list(range(inp['MARKS'].iloc[0],inp['MARKS'].iloc[-1]+1 )),columns = ['MARKS'] )
	names = txt.merge(inp,on='MARKS',how='outer')
	fin = names.groupby('MARKS')['Name'].apply( lambda x: ''.join(x.to_string(index=False))).str.replace('(\\n)', ',').reset_index()

	val = pd.DataFrame({'Grades':grades,'Value':cur_inp} ) 
	val = pd.DataFrame({'Grades':[''],'Value':[inp['MARKS'].iloc[-1]+1]}).append(val)
	val.index = [ i for i in range(0,len(val))]
	# print(val)
	traces.append(
	    go.Scatter( 
	        x = [ np.mean(inp['MARKS'] ),np.mean(inp['MARKS'] )],
	        y = [count,0],
	        # mode='lines',
	        name = 'Average : {:.2f}'.format( float(str(np.mean(inp['MARKS'])) ) ),
	        hoverinfo = 'name+x',
	        line={
	            'dash' : 'dash',
	            'color' : 'green'},
	    )
	)

	for i in val.index[1:]:
	    sec = inp.loc[ (inp['MARKS'] < val['Value'][i-1]) & (inp['MARKS'] >= val['Value'][i]) ]
	    for j in sec.index:
	        MGPA.append(marks[val['Grades'][i]])

	for i in val.index[1:]:
	    sec = inp.loc[ (inp['MARKS'] < val['Value'][i-1]) & (inp['MARKS'] >= val['Value'][i]) ]
	    ppl = fin.loc[ (fin['MARKS'] < val['Value'][i-1]) & (fin['MARKS'] >= val['Value'][i]) ]
	    ppl = ppl.loc[ ppl['MARKS'] >= sec["MARKS"].min() ]

	    low = val['Value'][i]
	    high = val['Value'][i-1]
	    mean = np.mean(MGPA)
	    diff = float( str( mean -int(mean) )[1:] )

	    if( marks[val['Grades'][i]] == int(np.mean(MGPA)) ):
	        x = low + diff*(high-low)

	    if( not sec.empty ):
	        traces.append(
	            go.Histogram(
	                x=sec['MARKS'],
	                name= val['Grades'][i] + " : " + str(val['Value'][i]) + ' - ' + str(val['Value'][i-1]-1),
	                text = (ppl['Name']),
	                hovertemplate = 'Marks: %{x}'
	                    '<br>No of students: %{y}<br>'
	                    '%{text}',
	                xbins=dict(size=1),
	                opacity=0.8
	            )   
	        )
	    traces.append( 
	        go.Scatter( 
	            x = [str(val['Value'][i]),str(val['Value'][i])],
	            y = [inp.groupby('MARKS').count().max()[0],0],
	            name = val['Grades'][i],
	            mode = 'lines+markers+text',
	            text = [val['Grades'][i]],
	            textposition = 'top left',
	            # marker_color=cl.scales['9']['qual']['Set1'][-1-i],
	            marker_color='gray',
	            showlegend = False,
	            hoverinfo = 'name+x'
	        )
	    )

	traces.append( go.Scatter( 
	    x = [ x,x ],
	    y = [count,0],
	    name = 'Marks corresponding to mean grade({:.2f})'.format( np.mean(MGPA) ) ,
	    hoverinfo = 'name+x',
	    line={
	            'dash' : 'dash',
	            'color' : 'blue'},
	) )
	# trace = [go.Histogram(
	#         x=[val1,val2,val3,val4,val5,val6,val7,val8,val9],
	#         xbins=dict(size=1),
	#         opacity=0.8
	#     )]
	return {
	    'data': traces,
	    'layout': dict(
	        # title_text='CHEM F311  Organic Chemistry', # title of plot
	        xaxis_title_text='Marks', # xaxis label
	        yaxis_title_text='No of students', # yaxis label
	        bargap=0.1, # gap between bars of adjacent location coordinates'
	        hovermode = 'closest',
	        xaxis = dict(
	            tickmode = 'linear',
	            tick0 = 0,
	            dtick = 2,

	            tickfont = dict(
	                size = 5
	            )
	    
	        )   
	    )
	}




external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

layout = [ ]

layout.append(dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files '),
        ]),
        style={
            'width': '90%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),)
layout.append( dcc.Markdown('''[Download example marksheet](https://drive.google.com/file/d/1Hrv3B4BJV57IR2fhp7HABz4kAzmbQYrf/view?usp=sharing) ''',style ={ 'textAlign': 'center', 'width' : '90%'}) )
layout.append( dcc.Graph( id = 'graph',style = { 'height':'80vh'}  ) )
# layout.append( dcc.RadioItems(
#     options=[ { 'label' : grade , 'value' : grade } for grade,val in marks.items() ],
#     labelStyle={
#     	'display': 'inline-block', 
#     	'margin': "0px 50px 50px 50px",
#     	'borderRadius': '5px',
#     	'height' : '20px',
#     	'padding' : '5px'
# 	},
# )  )
layout.append(
	html.Div(
		dcc.RangeSlider( 
			id = 'slider',
			marks = { 
			},
			className = "ten columns",
			pushable = 1,
			# tooltip = { 'always_visible' : True }
		),
		style = {
			"margin" : "60px 50px 160px 50px"
		}
	)
)

layout.append( html.Div(id='intermediate-value', style={'display': 'none'}) )

for i in range(len(grades)):
    layout.append( input_field( grades[i] ) )

app.layout = html.Div(layout)

init_op = []
init_op.append( Output( 'slider' , 'value') )
init_op.append( Output( 'slider' , 'min') )
init_op.append( Output( 'slider' , 'max') )
init_op.append( Output( 'slider' , 'marks') )
init_op.append( Output('intermediate-value', 'children') )
@app.callback(
	init_op,
	[Input('upload-data', 'contents')],
	[State('upload-data', 'filename'),
	State('upload-data', 'last_modified')]
)
def init(contents,s1,s2):
	inp = pd.DataFrame()
	cur_inp = list(range(10,0,-1))
	if contents is not None:  
		content_type, content_string = contents[0].split(',')
		decoded = base64.b64decode(content_string)
		inp = pd.read_excel(io.BytesIO(decoded))

		inp.dropna(subset=['Name', 'MARKS'],inplace=True)
		inp.sort_values(['MARKS'],inplace=True)
		diff = (int)( (inp['MARKS'].iloc[-1] - inp['MARKS'].iloc[0])/9 )

		cur_inp = [ inp['MARKS'].iloc[-1] - diff * (i+1) for i in range(len(grades)-1) ]
		cur_inp.append(0)
		# print(cur_inp[::-1],inp['MARKS'].iloc[-1],cur_inp)
		marks = { i : str(i) for i in range(0,int(inp['MARKS'].iloc[-1]+1),5)}

		return cur_inp[::-1],-14,inp['MARKS'].iloc[-1]+10,marks,inp.to_json()

	return cur_inp[::-1],0,10,{},inp.to_json()

# call_op = [ Output(i, 'value') for i in grades ]
@app.callback( [ Output(i, 'value') for i in grades ] , [ Input( 'slider', 'value' ) ] )
def update( inp ):
	if( inp == None ):
		inp = range(8,-1,-1)
	return inp[8],inp[7],inp[6],inp[5],inp[4],inp[3],inp[2],inp[1],inp[0]


call_inp = [ Input(i, 'value') for i in grades]
call_inp.append( Input('intermediate-value', 'children' ) )
@app.callback(
    Output('graph', 'figure'),
    call_inp,
)
def update_figure(val1,val2,val3,val4,val5,val6,val7,val8,val9,df):
	cur_inp = [val1,val2,val3,val4,val5,val6,val7,val8,val9]
	cur_inp = [ int(i) if(i) else 0 for i in cur_inp]
	
	
	if( df ):
		df = pd.read_json(df)
		# print(df)
		if( not df.empty):
			return graph(df,cur_inp)
	return {'data':[],'layout':{}}


if __name__ == '__main__':
	url = 'http://127.0.0.1:8050/'
	webbrowser.open_new(url)
	app.run_server(debug=True)



