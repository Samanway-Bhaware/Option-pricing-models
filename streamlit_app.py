import streamlit as st
from enum import Enum
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from option_pricing import BlackScholesModel, MonteCarloPricing, BinomialTreeModel, Ticker
import json

st.set_page_config( page_title="Option Price Models",
                    page_icon="📊",
                    layout="wide",
                    initial_sidebar_state="expanded")
st.markdown("""
<style>
/* Adjust the size and alignment of the CALL and PUT value containers */
.metric-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 8px; /* Adjust the padding to control height */
    width: auto; /* Auto width for responsiveness, or set a fixed width if necessary */
    margin: 0 auto; /* Center the container */
}

/* Custom classes for CALL and PUT values */
.metric-call {
    background-color: #90ee90; /* Light green background */
    color: black; /* Black font color */
    margin-right: 10px; /* Spacing between CALL and PUT */
    border-radius: 10px; /* Rounded corners */
}

.metric-put {
    background-color: #ffcccb; /* Light red background */
    color: black; /* Black font color */
    border-radius: 10px; /* Rounded corners */
}

/* Style for the value text */
.metric-value {
    font-size: 1.5rem; /* Adjust font size */
    font-weight: bold;
    margin: 0; /* Remove default margins */
}

/* Style for the label text */
.metric-label {
    font-size: 1rem; /* Adjust font size */
    margin-bottom: 4px; /* Spacing between label and value */
}

</style>
""", unsafe_allow_html=True)

class OPTION_PRICING_MODEL(Enum):
    BLACK_SCHOLES = 'Black Scholes Model'
    MONTE_CARLO = 'Monte Carlo Simulation'
    BINOMIAL = 'Binomial Model'

@st.cache_data
def get_historical_data(ticker):
    try:
        data = Ticker.get_historical_data(ticker)
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None

@st.cache_data
def get_current_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        company_name = yf.Ticker(ticker).info.get("longName", ticker)
        # print(data)
        return data['Close'].iloc[-1], company_name
    except Exception as e:
        st.error(f"Error fetching current price for {ticker}: {str(e)}")
        return None

st.sidebar.title("📊 Option pricing")
 
# User selected model from sidebar 
# pricing_method = st.sidebar.radio('Please select option pricing method', options=[model.value for model in OPTION_PRICING_MODEL])
#User selected model from sidebar dropdown
MODELS = [model.value for model in OPTION_PRICING_MODEL]
pricing_method = st.sidebar.selectbox("Choose model", MODELS)
# Displaying specified model
st.title(f'Pricing method: {pricing_method}') 

if pricing_method == OPTION_PRICING_MODEL.BLACK_SCHOLES.value:
    # Parameters for Black-Scholes model
    ticker = st.sidebar.text_input('Ticker symbol', 'AAPL')
    st.sidebar.caption("Enter the stock symbol (e.g., AAPL for Apple Inc.)")

    # Fetch current price
    current_price, company_name = get_current_price(ticker)
    
    if current_price is not None:
        st.sidebar.code(f"Current price of ${ticker} is ${current_price:.2f}", language=None)
        
        # Set default and min/max values based on current price
        default_strike = round(current_price, 2)
        min_strike = max(0.1, round(current_price * 0.5, 2))
        max_strike = round(current_price * 2, 2)
        
        strike_price = st.sidebar.number_input('Strike price', 
                                       min_value=min_strike, 
                                       max_value=max_strike, 
                                       value=default_strike, 
                                       step=0.01,help=f"The price at which the option can be exercised. Range: ${min_strike:.2f} <= Strike Price <= ${max_strike:.2f}")
        # st.sidebar.caption(f"The price at which the option can be exercised. Range: ${min_strike:.2f} to ${max_strike:.2f}")
    else:
        strike_price = st.sidebar.number_input('Strike price', min_value=0.01, value=100.0, step=0.01)
        st.caption("The price at which the option can be exercised. Enter a valid ticker to see a suggested range.")

    risk_free_rate = st.sidebar.slider('Risk-free rate (%)', 0, 100, 10, help="The theoretical rate of return of an investment with zero risk. Usually based on government bonds. 0% means no risk-free return, 100% means doubling your money risk-free (unrealistic).")
    # st.sidebar.caption("The theoretical rate of return of an investment with zero risk. Usually based on government bonds. 0% means no risk-free return, 100% means doubling your money risk-free (unrealistic).")

    sigma = st.sidebar.slider('Sigma (Volatility) (%)', 0, 100, 20, help="A measure of the stock's price variability. Higher values indicate more volatile stocks. 0% means no volatility (unrealistic), 100% means extremely volatile.")
    # st.sidebar.caption("A measure of the stock's price variability. Higher values indicate more volatile stocks. 0% means no volatility (unrealistic), 100% means extremely volatile.")

    exercise_date = st.sidebar.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365))
    st.sidebar.caption("The date when the option can be exercised")
    
    if st.sidebar.button(f'Calculate option price for {company_name}', type="primary"):
        try:
            with st.spinner('Fetching data...'):
                data = get_historical_data(ticker)

            if data is not None and not data.empty:
                
                spot_price = Ticker.get_last_price(data, 'Close')
                risk_free_rate = risk_free_rate / 100
                sigma = sigma / 100
                days_to_maturity = (exercise_date - datetime.now().date()).days

                BSM = BlackScholesModel(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma)
                call_option_price = BSM.calculate_option_price('Call Option')
                put_option_price = BSM.calculate_option_price('Put Option')

                # Table of Inputs
                input_data = {
                        "Current Asset Price": [current_price],
                        "Strike Price": [strike_price],
                        "Time to Maturity (Years)": [days_to_maturity/365],
                        "Volatility (σ)": [sigma],
                        "Risk-Free Interest Rate": [risk_free_rate],
                    }
                input_df = pd.DataFrame(input_data)
                st.table(input_df)
                # Display Call and Put Values in colored tables
                col1, col2 = st.columns([1,1], gap="small")

                with col1:
                    # Using the custom class for CALL value
                    st.markdown(f"""
                        <div class="metric-container metric-call">
                            <div>
                                <div class="metric-label">CALL Value</div>
                                <div class="metric-value">${call_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Using the custom class for PUT value
                    st.markdown(f"""
                        <div class="metric-container metric-put">
                            <div>
                                <div class="metric-label">PUT Value</div>
                                <div class="metric-value">${put_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.write("Data fetched successfully:")
                st.write(data.tail())
                
                fig = Ticker.plot_data(data, ticker, 'Close')
                st.pyplot(fig)

            else: 
                st.error("Unable to proceed with calculations due to data fetching error.")
        except Exception as e:
            st.error(f"Error during calculation: {str(e)}")
    else:
        st.info("Click 'Calculate option price' to see results.")

elif pricing_method == OPTION_PRICING_MODEL.MONTE_CARLO.value:
    # Parameters for Monte Carlo simulation
    ticker = st.sidebar.text_input('Ticker symbol', 'AAPL')
    st.sidebar.caption("Enter the stock symbol (e.g., AAPL for Apple Inc.)")

    # Fetch current price
    current_price, company_name = get_current_price(ticker)
    
    if current_price is not None:
        st.sidebar.write(f"Current price of {ticker}: ${current_price:.2f}")
        
        # Set default and min/max values based on current price
        default_strike = round(current_price, 2)
        min_strike = max(0.1, round(current_price * 0.5, 2))
        max_strike = round(current_price * 2, 2)
        
        strike_price = st.sidebar.number_input('Strike price', 
                                       min_value=min_strike, 
                                       max_value=max_strike, 
                                       value=default_strike, 
                                       step=0.01, help=f"The price at which the option can be exercised. Range: ${min_strike:.2f} <= Strike Price <= ${max_strike:.2f}")
        # st.sidebar.caption(f"The price at which the option can be exercised. Range: ${min_strike:.2f} to ${max_strike:.2f}")
    else:
        strike_price = st.sidebar.number_input('Strike price', min_value=0.01, value=100.0, step=0.01)
        st.caption("The price at which the option can be exercised. Enter a valid ticker to see a suggested range.")

    risk_free_rate = st.sidebar.slider('Risk-free rate (%)', 0, 100, 10, help="The theoretical rate of return of an investment with zero risk. Usually based on government bonds. 0% means no risk-free return, 100% means doubling your money risk-free (unrealistic).")

    sigma = st.sidebar.slider('Sigma (Volatility) (%)', 0, 100, 20, help="A measure of the stock's price variability. Higher values indicate more volatile stocks. 0% means no volatility (unrealistic), 100% means extremely volatile.")

    exercise_date = st.sidebar.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365), help="The date when the option can be exercised")

    number_of_simulations = st.sidebar.slider('Number of simulations', 100, 100000, 10000, help="The number of price paths to simulate. More simulations increase accuracy but take longer to compute.")

    num_of_movements = st.sidebar.slider('Number of price movement simulations to be visualized ', 0, int(number_of_simulations/10), 100, help="The number of simulated price paths to display on the graph")

    if st.sidebar.button(f'Calculate option price for {company_name}', type="primary"):
        try:
            with st.spinner('Fetching data...'):
                data = get_historical_data(ticker)
            
            if data is not None and not data.empty:
                
                # fig = Ticker.plot_data(data, ticker, 'Close')
                # st.pyplot(fig)

                spot_price = Ticker.get_last_price(data, 'Close')
                risk_free_rate = risk_free_rate / 100
                sigma = sigma / 100
                days_to_maturity = (exercise_date - datetime.now().date()).days

                MC = MonteCarloPricing(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_simulations)
                MC.simulate_prices()
                


                call_option_price = MC.calculate_option_price('Call Option')
                put_option_price = MC.calculate_option_price('Put Option')
                # Table of Inputs
                input_data = {
                        "Current Asset Price": [current_price],
                        "Strike Price": [strike_price],
                        "Time to Maturity (Years)": [days_to_maturity/365],
                        "Volatility (σ)": [sigma],
                        "Risk-Free Interest Rate": [risk_free_rate],
                    }
                input_df = pd.DataFrame(input_data)
                st.table(input_df)
                # Display Call and Put Values in colored tables
                col1, col2 = st.columns([1,1], gap="small")

                with col1:
                    # Using the custom class for CALL value
                    st.markdown(f"""
                        <div class="metric-container metric-call">
                            <div>
                                <div class="metric-label">CALL Value</div>
                                <div class="metric-value">${call_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Using the custom class for PUT value
                    st.markdown(f"""
                        <div class="metric-container metric-put">
                            <div>
                                <div class="metric-label">PUT Value</div>
                                <div class="metric-value">${put_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                st.write("Data fetched successfully:")
                st.write(data.tail())

                fig1 = MC.plot_simulation_results(num_of_movements)  
                st.pyplot(fig1)                                      

                fig2 = Ticker.plot_data(data, ticker, 'Close')
                st.pyplot(fig2)

            else:
                st.sidebar.error("Unable to proceed with calculations due to data fetching error.")
        except Exception as e:
            st.sidebar.error(f"Error during calculation: {str(e)}")
    else:
        st.info("Click 'Calculate option price' to see results.")

elif pricing_method == OPTION_PRICING_MODEL.BINOMIAL.value:
    # Parameters for Binomial-Tree model
    ticker = st.sidebar.text_input('Ticker symbol', 'AAPL')
    st.sidebar.caption("Enter the stock symbol (e.g., AAPL for Apple Inc.)")

    # Fetch current price
    current_price, company_name = get_current_price(ticker)
    
    if current_price is not None:
        st.sidebar.write(f"Current price of {ticker}: ${current_price:.2f}")
        
        # Set default and min/max values based on current price
        default_strike = round(current_price, 2)
        min_strike = max(0.1, round(current_price * 0.5, 2))
        max_strike = round(current_price * 2, 2)
        
        strike_price = st.sidebar.number_input('Strike price', 
                                       min_value=min_strike, 
                                       max_value=max_strike, 
                                       value=default_strike, 
                                       step=0.01, help=f"The price at which the option can be exercised. Range: ${min_strike:.2f} <= Strike Price <= ${max_strike:.2f}")
       
    else:
        strike_price = st.number_input('Strike price', min_value=0.01, value=100.0, step=0.01, help="The price at which the option can be exercised. Enter a valid ticker to see a suggested range.")

    risk_free_rate = st.sidebar.slider('Risk-free rate (%)', 0, 100, 10, help="The theoretical rate of return of an investment with zero risk. Usually based on government bonds. 0% means no risk-free return, 100% means doubling your money risk-free (unrealistic).")

    sigma = st.sidebar.slider('Sigma (Volatility) (%)', 0, 100, 20, help="A measure of the stock's price variability. Higher values indicate more volatile stocks. 0% means no volatility (unrealistic), 100% means extremely volatile.")

    exercise_date = st.sidebar.date_input('Exercise date', min_value=datetime.today() + timedelta(days=1), value=datetime.today() + timedelta(days=365), help="The date when the option can be exercised")

    number_of_time_steps = st.sidebar.slider('Number of time steps', 5000, 100000, 15000, help="The number of periods in the binomial tree. More steps increase accuracy but take longer to compute.")

    if st.sidebar.button(f'Calculate option price for {company_name}', type="primary"):
        try:
            with st.spinner('Fetching data...'):
                data = get_historical_data(ticker)
            
            if data is not None and not data.empty:

                spot_price = Ticker.get_last_price(data, 'Close')
                risk_free_rate = risk_free_rate / 100
                sigma = sigma / 100
                days_to_maturity = (exercise_date - datetime.now().date()).days

                BOPM = BinomialTreeModel(spot_price, strike_price, days_to_maturity, risk_free_rate, sigma, number_of_time_steps)
                call_option_price = BOPM.calculate_option_price('Call Option')
                put_option_price = BOPM.calculate_option_price('Put Option')
                # Table of Inputs
                input_data = {
                        "Current Asset Price": [current_price],
                        "Strike Price": [strike_price],
                        "Time to Maturity (Years)": [days_to_maturity/365],
                        "Volatility (σ)": [sigma],
                        "Risk-Free Interest Rate": [risk_free_rate],
                    }
                input_df = pd.DataFrame(input_data)
                st.table(input_df)
                # Display Call and Put Values in colored tables
                col1, col2 = st.columns([1,1], gap="small")

                with col1:
                    # Using the custom class for CALL value
                    st.markdown(f"""
                        <div class="metric-container metric-call">
                            <div>
                                <div class="metric-label">CALL Value</div>
                                <div class="metric-value">${call_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Using the custom class for PUT value
                    st.markdown(f"""
                        <div class="metric-container metric-put">
                            <div>
                                <div class="metric-label">PUT Value</div>
                                <div class="metric-value">${put_option_price:.2f}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                st.write("Data fetched successfully:")
                st.write(data.tail())
                
                fig = Ticker.plot_data(data, ticker, 'Close')
                st.pyplot(fig)
                
            else:
                st.error("Unable to proceed with calculations due to data fetching error.")
        except Exception as e:
            st.error(f"Error during calculation: {str(e)}")
    else:
        st.info("Click 'Calculate option price' to see results.")

