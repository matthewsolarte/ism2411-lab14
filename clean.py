# Reflection
#
# 1. The most ambiguous choice is filling missing quantity_sold with the mean.
#    It keeps the rows, but the filled number is a guess, and a guessed
#    quantity changes revenue. Before doing this on real data I would ask the
#    order system team whether a blank quantity means 1 item, 0 items, or a
#    failed export, and whether the warehouse has the true counts.
#
# 2. I rewrote my comments so each one says why, not only what. For example,
#    the comment on dropping rows missing order_id says the row cannot be
#    traced or matched to anything without an ID, instead of only saying
#    "drop rows missing order_id".
#
# 3. After describe() I did not expect the quantity_sold max of 9,999, which
#    pulled the mean far above the median. I also did not expect negative
#    unit prices, which turned out to be returns, and a few orders with a
#    quantity of 0.

import pandas as pd


# Exercise 1: Inspect
print("Exercise 1: inspect")
df = pd.read_csv("data/messy_sales.csv")
df.info()
print(df.isnull().sum())

# Data quality issues found:
# - Unit Price is stored as text like "$1,299.00", so it is not a number yet.
# - Order Date is text with mixed formats (2025-01-15, 01/15/2025,
#   March 20 2025) plus junk values like TBD, unknown, and 00/00/0000.
# - Quantity Sold is float instead of int because 94 values are missing.
# - Customer ID is missing in 362 rows (about 7.5%), Region in 111 rows,
#   Order ID in 31 rows, and Order Date in 25 rows.
# - Some orders appear twice because they were exported twice.


# Exercise 2: Standardize column names
print()
print("Exercise 2: column names")
df.columns = df.columns.str.lower().str.replace(" ", "_")
print(df.columns.tolist())


# Exercise 3: Handle missing values
print()
print("Exercise 3: missing values")
print("Shape before:", df.shape)

# quantity_sold is the only numeric column with gaps, and only about 2% of
# rows are missing. Filling with the mean keeps those orders in the data
# instead of losing their price, region, and category. The 9,999 placeholder
# rows are left out of the mean so they do not inflate it.
real_qty = df.loc[df["quantity_sold"] != 9999, "quantity_sold"]
df["quantity_sold"] = df["quantity_sold"].fillna(round(real_qty.mean()))

# Without an order_id a row cannot be traced back to the order system or
# checked for duplicates. Without an order_date it cannot be used in any
# time based analysis. Both are essential, so those rows are dropped.
df = df.dropna(subset=["order_id", "order_date"])

# Missing region and customer_id are kept as blanks. The orders are still
# real sales, and dropping 7% of rows just for a missing customer would
# understate revenue.
print("Shape after:", df.shape)
print(df[["quantity_sold", "order_id", "order_date"]].isnull().sum())


# Exercise 4: Fix types
print()
print("Exercise 4: fix types")

# pandas guesses one date format from the first row, so 01/15/2025 and
# March 20 2025 would become NaT and real orders would be lost. format="mixed"
# reads each value on its own. Junk like TBD and 00/00/0000 still becomes NaT.
df["order_date"] = pd.to_datetime(df["order_date"], format="mixed", errors="coerce")
print("Dates that became NaT:", df["order_date"].isna().sum())

# A NaT date is the same as a missing date, so those rows are dropped for the
# same reason as above.
df = df.dropna(subset=["order_date"])

# Strip $ and commas so the text can be read as a number. A minus sign stays,
# so "-$45.00" becomes -45.0, which marks a return.
df["unit_price"] = (
    df["unit_price"].str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
    .astype(float)
)

df["quantity_sold"] = df["quantity_sold"].astype(int)
df["revenue"] = (df["unit_price"] * df["quantity_sold"]).round(2)
print(df.dtypes)


# Exercise 5: Check duplicates
print()
print("Exercise 5: duplicates")
print("Duplicate rows:", df.duplicated().sum())
# Each duplicate is the same order exported twice, so keeping both would
# count the sale twice.
df = df.drop_duplicates()
print("Shape:", df.shape)


# Exercise 6: Describe
print()
print("Exercise 6: describe")
print(df.describe())

# Suspicious statistics:
# - quantity_sold has a max of 9,999 while the median is about 3. This is a
#   placeholder the old system used for an unknown quantity, not a real order.
# - unit_price and revenue have negative minimums. These are returns, where
#   money went back to the customer.
# - The mean quantity_sold is well above the median, because a few huge
#   values pull the mean up.

# 9,999 is a placeholder, not a real order. Keeping it would add millions in
# fake revenue, so those rows are dropped.
df = df[df["quantity_sold"] != 9999]

# Negative revenues are kept because they are real returns, and removing them
# would overstate net sales.
print("Shape after removing 9,999 placeholders:", df.shape)


# Exercise 7: Save
print()
print("Exercise 7: save")
df.to_csv("data/clean_sales.csv", index=False)
clean = pd.read_csv("data/clean_sales.csv", parse_dates=["order_date"])
clean.info()
