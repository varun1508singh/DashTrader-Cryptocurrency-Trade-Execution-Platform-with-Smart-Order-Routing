import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

external_stylesheets = ["https://fonts.googleapis.com/css?family=Merriweather+Sans:400,700",
                        "https://fonts.googleapis.com/css?family=Merriweather:400,300,300italic,400italic,700,700italic"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, meta_tags=[{"name": "viewport",
                                                                                 "content": "width=device-width"}])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

index_page = html.Header(children=
                         html.Div(children=
                                  html.Div(children=[html.Div(children=[html.H1(children='Smart Order Router',
                                                                                className="text-uppercase text-white "
                                                                                          "font-weight-bold"),
                                                                        html.Hr(className="divider my-4")],
                                                              className="col-lg-10 align-self-end"), html.Div(children=[
                                      html.P(
                                          children="Our Application routes your order to execute at the best possible "
                                                   "price by comparing different exchanges",
                                          className="text-white-75 font-weight-light mb-5"),
                                      html.A(children="Trade NOW!!!", href="/page-1",
                                             className="btn btn-primary btn-xl js-scroll-trigger")],
                                      className="col-lg-8 align-self-baseline")],
                                           className="row h-100 align-items-center justify-content-center text-center")
                                  , className="container h-100")
                         , className="masthead")


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return page_1_layout
    else:
        return index_page


page_1_layout = html.Div([
    html.H1('Page 1'),
    dcc.Dropdown(
        id='page-1-dropdown',
        options=[{'label': i, 'value': i} for i in ['LA', 'NYC', 'MTL']],
        value='LA'
    ),
    html.Div(id='page-1-content'),
    html.Br(),
    dcc.Link('Go back to home', href='/'),
])

if __name__ == '__main__':
    app.run_server(debug=True)
