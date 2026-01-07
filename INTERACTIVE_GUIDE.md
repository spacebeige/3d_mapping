# 🏭 Interactive Warehouse Builder - Quick Start Guide

## Overview

This guide helps you create a custom warehouse digital twin step-by-step:
1. **Define warehouse dimensions** - Length, width, height, number of aisles
2. **Add products individually** - Enter products one at a time with details
3. **Automatic positioning** - Each product gets a unique 3D position
4. **Visualize in 3D** - See your warehouse with all products displayed
5. **Download files** - Get HTML visualizations and CSV data

## 🚀 Two Ways to Use

### Option 1: Interactive Jupyter Notebook (Recommended)

**Best for:** Visual learners, data exploration, Google Colab users

```bash
# Install and run
jupyter notebook examples/interactive_warehouse.ipynb
```

**Features:**
- ✅ Step-by-step cells with explanations
- ✅ Interactive input prompts
- ✅ Immediate visualization
- ✅ Works in Google Colab
- ✅ Great for learning

### Option 2: Command-Line Script

**Best for:** Automation, scripting, command-line users

```bash
# Run directly
python interactive_warehouse.py
```

**Features:**
- ✅ Same functionality as notebook
- ✅ Faster for repeat runs
- ✅ Can be automated
- ✅ No Jupyter required
- ✅ Terminal-friendly

## 📝 Step-by-Step Walkthrough

### Step 1: Define Warehouse Dimensions

You'll be prompted for:

```
🏗️ WAREHOUSE CONFIGURATION
==================================================
Enter warehouse name (default: My Distribution Center): 
Enter warehouse length in meters (default: 100): 
Enter warehouse width in meters (default: 80): 
Enter warehouse height in meters (default: 10): 
Enter number of aisles (default: 10): 
```

**Example Input:**
```
Enter warehouse name: Tech Warehouse
Enter warehouse length in meters: 150
Enter warehouse width in meters: 100
Enter warehouse height in meters: 12
Enter number of aisles: 20
```

**What happens:**
- Creates warehouse structure with specified dimensions
- Generates aisles, racks, and shelves
- Calculates total storage capacity
- Prepares for product allocation

### Step 2: Add Products

For each product, enter:

```
📦 PRODUCT INPUT
==================================================
--- Product #1 ---
Product ID (default: PROD0001, or 'done' to finish): 
Category (electronics/groceries/pharma/apparel/automotive): 
Description: 
Stock level (default: 100): 
Daily demand (default: 10): 
```

**Example Product:**
```
Product ID: LAPTOP-HP-001
Category: electronics
Description: HP Laptop 15.6 inch
Stock level: 50
Daily demand: 5

✅ Product added!
   ID: LAPTOP-HP-001
   Position: (12.50, 15.00, 2.40)
   Zone: C
```

**Key Points:**
- Each product gets a **unique position** (x, y, z coordinates)
- Products never overlap
- Position is calculated automatically
- Zone assigned based on demand:
  - **Zone A**: High demand (>50 units/day)
  - **Zone B**: Medium demand (20-50 units/day)
  - **Zone C**: Normal demand (10-20 units/day)
  - **Zone D**: Low demand (<10 units/day)

### Step 3: Continue or Finish

After each product:
```
Add another product? (y/n, default: y): 
```

- Type `y` or press Enter to add more products
- Type `n` to finish and proceed to visualization

Or type `done` as the Product ID to finish.

### Step 4: View Summary

You'll see a table with all products:

```
📋 PRODUCT SUMMARY
================================================================================
Product ID       Category     Description              Stock  Daily Demand  Zone  Position X  Position Y  Position Z
LAPTOP-HP-001    electronics  HP Laptop 15.6 inch        50          5.00  C         12.50       15.00        2.40
PHONE-APP-001    electronics  iPhone 15 Pro             200         80.00  A         25.00       15.00        2.40
TABLET-SAM-001   electronics  Samsung Galaxy Tab        120         25.00  B         37.50       15.00        2.40
...
```

Plus statistics:
```
📊 STATISTICS
==================================================
Total Products: 3
Total Stock: 370 units
Total Daily Demand: 110.0 units/day

Zone Distribution:
  Zone A: 1 products
  Zone B: 1 products
  Zone C: 1 products
```

### Step 5: 3D Visualization

The system automatically generates:

```
🎨 Generating 3D warehouse visualization...
✅ Visualization generated!
```

**What you can do:**
- **Rotate**: Click and drag
- **Zoom**: Scroll or pinch
- **Pan**: Shift + drag
- **Hover**: See product details (ID, zone, category)
- **Click legend**: Show/hide products by zone

### Step 6: Download Files

Three files are created:

```
💾 Saving files...
✅ Saved: warehouse_3d.html
✅ Saved: products.csv
✅ Saved: dashboard.html
```

**Files:**
1. **warehouse_3d.html** - Interactive 3D visualization
   - Open in any web browser
   - Fully interactive
   - Shows all products with unique positions
   
2. **products.csv** - Product data table
   - Import into Excel/Google Sheets
   - Contains all product info + positions
   - Use for reports or analysis
   
3. **dashboard.html** - Analytics dashboard (if products loaded)
   - Performance metrics
   - Zone utilization
   - Demand analysis

## 💡 Tips & Tricks

### Quick Start with Defaults

Press Enter to accept defaults for fast setup:
```
Enter warehouse name: [Enter]  # Uses "My Distribution Center"
Enter warehouse length: [Enter]  # Uses 100m
Enter warehouse width: [Enter]  # Uses 80m
...
```

### Sample Products

If you don't enter any products, the system automatically adds 5 sample products.

### Position Algorithm

Products are distributed using dynamic calculations based on warehouse dimensions:
- **Across aisles**: Products spread across all aisles
- **Along racks**: Dynamic - 1 rack per 5m of length (e.g., 100m = 20 racks)
- **On shelves**: Dynamic - 1 shelf per 1.6m of usable height (e.g., 8m usable = 5 shelves)
- **Formula**: `position = f(product_index, num_aisles, dimensions)`

Example for 100m × 80m × 10m warehouse with 10 aisles:
- Racks per aisle: 20 (100m ÷ 5)
- Shelves per rack: 5 (8m usable ÷ 1.6)
- Products 1-5: Aisle 1, Rack 1, Shelves 1-5
- Products 6-10: Aisle 1, Rack 2, Shelves 1-5
- Product 101: Aisle 2, Rack 1, Shelf 1

Different warehouse sizes scale automatically:
- 200m warehouse → 40 racks/aisle
- 50m warehouse → 10 racks/aisle

### Zone Assignment Logic

```python
if daily_demand > 50:   → Zone A (High-Value, High-Turnover)
elif daily_demand > 20: → Zone B (Medium-Value)
elif daily_demand > 10: → Zone C (Normal)
else:                   → Zone D (Long-Term Storage)
```

Zone A products are placed closest to exits for fastest picking.

## 🎯 Example Session

Complete example with real data:

```bash
$ python interactive_warehouse.py

============================================================
🏭 INTERACTIVE WAREHOUSE DIGITAL TWIN BUILDER
============================================================

🏗️ WAREHOUSE CONFIGURATION
==================================================
Enter warehouse name: Electronics Distribution Center
Enter warehouse length in meters: 120
Enter warehouse width in meters: 80
Enter warehouse height in meters: 10
Enter number of aisles: 15

📊 Warehouse Configuration:
   Name: Electronics Distribution Center
   Dimensions: 120m × 80m × 10m
   Aisles: 15
   Volume: 96,000 m³

🏗️ Creating warehouse...
✅ Warehouse created successfully!

📦 PRODUCT INPUT
==================================================
Enter product details. Type 'done' when finished.

--- Product #1 ---
Product ID: LAPTOP-DELL-XPS
Category: electronics
Description: Dell XPS 13 Laptop
Stock level: 60
Daily demand: 25

✅ Product added!
   ID: LAPTOP-DELL-XPS
   Position: (5.33, 3.00, 2.00)
   Zone: B

Add another product? (y/n): y

--- Product #2 ---
Product ID: IPHONE-15-PRO
Category: electronics
Description: Apple iPhone 15 Pro
Stock level: 200
Daily demand: 80

✅ Product added!
   ID: IPHONE-15-PRO
   Position: (10.67, 3.00, 2.00)
   Zone: A

Add another product? (y/n): y

--- Product #3 ---
Product ID: USB-CABLE-C
Category: electronics
Description: USB-C Cable 2m
Stock level: 500
Daily demand: 5

✅ Product added!
   ID: USB-CABLE-C
   Position: (16.00, 3.00, 2.00)
   Zone: D

Add another product? (y/n): n

✅ Total products added: 3

📋 PRODUCT SUMMARY
...

🎨 Generating 3D warehouse visualization...
✅ Visualization generated!

💾 Saving files...
✅ Saved: warehouse_3d.html
✅ Saved: products.csv
✅ Saved: dashboard.html

============================================================
🎉 WAREHOUSE DIGITAL TWIN CREATED SUCCESSFULLY!
============================================================

✅ What you've created:
   • Warehouse: Electronics Distribution Center
   • Dimensions: 120m × 80m × 10m
   • Aisles: 15
   • Products: 3
   • Files: warehouse_3d.html, products.csv, dashboard.html

💡 Next steps:
   1. Open warehouse_3d.html in your browser
   2. Explore the 3D visualization (rotate, zoom, click)
   3. Check products.csv for all product data
   4. View dashboard.html for analytics
```

## 🔧 Troubleshooting

### Issue: "Module not found" errors

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Can't see products in visualization

**Cause:** Products might be outside view or colors blend in

**Solution:**
- Rotate the view (click and drag)
- Zoom out (scroll)
- Check legend to ensure products are not hidden
- Hover over different areas to find products

### Issue: Positions overlap

**Not possible!** The algorithm ensures unique positions for each product based on their index.

### Issue: Want to add more products later

**Solution:** Re-run the script and add all products again, OR:
1. Edit `products.csv` manually
2. Create a new visualization from CSV using `warehouse_demo.ipynb`

### Issue: Jupyter notebook doesn't prompt for input

**Cause:** Running in non-interactive environment

**Solution:** 
- Use Jupyter Notebook (not JupyterLab without extensions)
- Or use the command-line script instead: `python interactive_warehouse.py`

## 📚 Next Steps

After creating your warehouse:

1. **Explore the 3D visualization**
   - Open `warehouse_3d.html` in Chrome, Firefox, or Safari
   - Try rotating, zooming, and clicking on products
   - Each product shows its unique ID on hover

2. **Analyze the data**
   - Open `products.csv` in Excel or Google Sheets
   - Sort by zone, demand, or position
   - Calculate statistics or create reports

3. **Share with team**
   - Send HTML files via email (they're standalone)
   - Upload to cloud storage
   - Embed in presentations

4. **Advanced features**
   - Try the full demo notebook: `warehouse_demo.ipynb`
   - Load products from CSV
   - Run optimization algorithms
   - Create geospatial maps
   - Simulate AGV pathfinding

## 🎓 Learning Resources

- **Main README**: `/README.md` - Project overview
- **Examples README**: `/examples/README.md` - Detailed notebook guide
- **API Documentation**: Check docstrings in source code
- **Sample CSV**: `test_data_unseen_expanded.csv` (if available)

## 🤝 Support

Having issues? Try these steps:

1. ✅ Check this guide thoroughly
2. ✅ Review error messages carefully
3. ✅ Ensure all dependencies are installed
4. ✅ Try the command-line version if notebook fails
5. ✅ Check GitHub issues for similar problems

---

**Happy warehouse building!** 🏗️✨

Built with ❤️ using Python, Plotly, and Pydantic
