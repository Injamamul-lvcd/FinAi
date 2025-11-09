from fpdf import FPDF

# Create a PDF object
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

# Title
pdf.add_page()
pdf.set_font('Arial', 'B', 16)
pdf.cell(200, 10, 'Educational Summary: Finance Terms and Stock Market Concepts (Indian Market)', ln=True, align='C')
pdf.ln(10)

# Introduction
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '1. Introduction to the Indian Stock Market', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
The Indian stock market is one of the largest and most actively traded markets in the world. 
It consists primarily of two exchanges: the Bombay Stock Exchange (BSE) and the National Stock Exchange (NSE).
The major stock market indices include the Sensex (BSE) and Nifty (NSE), which represent the overall health and performance of the market.

Key Indian stock market terms:
- Sensex: The benchmark index of the BSE.
- Nifty: The benchmark index of the NSE.
- BSE: Bombay Stock Exchange.
- NSE: National Stock Exchange.
''')
pdf.ln(10)

# Key Financial Terms
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '2. Key Financial Terms', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
- **Stock**: A share in the ownership of a company, which gives the holder a claim to the company's profits and assets.
- **Bond**: A debt security issued by a company or government, where the issuer promises to pay interest and repay the principal at a later date.
- **ETF (Exchange-Traded Fund)**: A fund that holds a portfolio of stocks or other assets and is traded on stock exchanges.
- **Mutual Fund**: A pooled investment vehicle that collects money from multiple investors to invest in a diversified portfolio of assets.

- **Dividend**: A portion of a company’s profit paid to shareholders.
- **Capital Gains**: The profit made from the sale of an asset such as stock or real estate.
- **Earnings Per Share (EPS)**: A financial metric indicating the profitability of a company, calculated as net income divided by the number of outstanding shares.
''')
pdf.ln(10)

# Stock Market Operations
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '3. Stock Market Operations', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
The stock market operates through a system of buying and selling shares of companies. 
Shares are traded through brokers on stock exchanges, with prices determined by supply and demand. 
The Securities and Exchange Board of India (SEBI) regulates the market to ensure fairness and transparency.

Key players in the stock market:
- **Investors**: Individuals or institutions who buy and sell shares.
- **Brokers**: Entities that facilitate buying and selling of stocks.
- **Regulators**: Government bodies like SEBI that ensure the market operates fairly.
''')
pdf.ln(10)

# Types of Investors
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '4. Types of Investors', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
- **Retail Investors**: Individual investors who buy and sell stocks on their own behalf.
- **Institutional Investors**: Large organizations like mutual funds, pension funds, and insurance companies that invest substantial amounts of money.
- **Risk Tolerance**: Investors can choose between high-risk (equities) or low-risk (bonds) investments depending on their risk appetite.
- **Investment Strategies**: Growth investing, value investing, income investing, etc.
''')
pdf.ln(10)

# Market Trends & Analysis
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '5. Understanding Market Trends & Analysis', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
- **Bull Market**: A market where stock prices are rising or expected to rise.
- **Bear Market**: A market where stock prices are falling or expected to fall.
- **Technical Analysis**: An analysis method based on past market data, primarily price and volume.
- **Fundamental Analysis**: An analysis method that evaluates a company’s financial health and prospects by examining its financial statements, industry position, and macroeconomic factors.
''')
pdf.ln(10)

# Popular Investment Options in India
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '6. Popular Investment Options in India', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
1. **Equity (Stocks)**: Investment in individual company stocks.
2. **Mutual Funds**: A popular investment option for those looking for diversification without much hands-on management.
3. **Fixed Deposits (FDs)**: Low-risk, fixed-income investment, offering guaranteed returns.
4. **Real Estate**: Property investment has been a long-standing favorite in India.

A popular investment strategy is **Systematic Investment Plan (SIP)**, where investors contribute a fixed amount to a mutual fund regularly, benefiting from rupee cost averaging.
''')
pdf.ln(10)

# Case Study (Example)
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '7. Case Study: Reliance Industries', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
Reliance Industries, one of India’s largest conglomerates, has demonstrated consistent growth over the past decade. 
Here’s an example of how an investor might analyze its performance:
- **Stock Performance**: Reliance has seen an increase in stock price by 50% over the past year.
- **Key Metrics**: 
  - EPS: ₹93.22
  - Market Capitalization: ₹16.5 trillion
  - Dividend Yield: 1.2%
  
This demonstrates how investors can evaluate a company’s financial health and potential for growth.
''')
pdf.ln(10)

# Conclusion
pdf.set_font('Arial', 'B', 12)
pdf.cell(200, 10, '8. Conclusion', ln=True)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, '''
The Indian stock market offers numerous opportunities for investors. Understanding key terms, operations, and analysis methods 
is essential for making informed investment decisions. 

For beginners, starting with mutual funds or SIPs may be a less risky way to enter the market. 
As you gain more experience, you can explore direct equity investments and other asset classes.

The future outlook of the Indian stock market remains positive, with continued growth in sectors like technology, infrastructure, and consumer goods.
''')

# Save the PDF file
pdf_output_path = "Financial_Education_Summary_Indian_Market.pdf"
pdf.output(pdf_output_path)

print(f"PDF generated and saved as {pdf_output_path}")
