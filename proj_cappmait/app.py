import sys
from proj_cappmait.product import dashboard, analysis

def run_dashboard():
    app = dashboard.app
    app.run_server(debug=True, port=3009)

def run_analysis():
    app = analysis.app
    app.run_server(debug=True, port=3008)

def run():
    '''
    User type some arguments and we run a program

    '''
    print("Welcome! to our Trade Dashboads and Analysis program")
    user_input = input(
        '''Please type 'dashboard' for Dashboards, 
            'analysis' for analysis, 'quit' for quit program
        ''')
    if user_input == 'dashboard':
        run_dashboard()
    elif user_input == "analysis":
        run_analysis()
    elif user_input == 'quit':
        sys.exit()