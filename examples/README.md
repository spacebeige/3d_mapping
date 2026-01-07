# 🏭 Warehouse Demo Notebooks - Usage Guide

## Overview
This directory contains interactive notebooks for the Warehouse Digital Twin system:

1. **`interactive_warehouse.ipynb`** - **NEW!** Step-by-step interactive builder
   - Prompts for warehouse dimensions
   - Interactive product entry (one by one)
   - Automatic unique position assignment
   - Perfect for custom warehouse creation

2. **`warehouse_demo.ipynb`** - Complete system demonstration
   - Widget-based configuration
   - Batch product loading (CSV or sample data)
   - Full feature showcase
   - Advanced analytics and visualizations

## 🚀 Quick Start

### Which Notebook Should I Use?

**Use `interactive_warehouse.ipynb` if you want to:**
- ✅ Build your warehouse step-by-step with prompts
- ✅ Add products interactively (one at a time)
- ✅ Have each product automatically positioned
- ✅ Learn as you go with guided workflow

**Use `warehouse_demo.ipynb` if you want to:**
- ✅ Configure warehouse with visual widgets
- ✅ Load many products at once from CSV
- ✅ See all features in one demo
- ✅ Advanced analytics and geospatial maps

### Option 1: Local Setup (Recommended)

#### Prerequisites
- Python 3.9 or higher
- pip package manager

#### Step 1: Clone the Repository
```bash
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping
```

#### Step 2: Install Dependencies
```bash
# Install required packages
pip install -r requirements.txt

# Alternatively, install just the core dependencies:
pip install numpy pandas plotly scikit-learn ipywidgets ipython pydantic networkx
```

#### Step 3: Launch Jupyter Notebook
```bash
# For interactive step-by-step builder (RECOMMENDED FOR BEGINNERS)
jupyter notebook examples/interactive_warehouse.ipynb

# For complete demo with widgets
jupyter notebook examples/warehouse_demo.ipynb

# Or use JupyterLab
jupyter lab examples/interactive_warehouse.ipynb
```

#### Step 4: Run the Notebook
1. **Run All Cells Sequentially**: Click `Cell` → `Run All` in the menu
2. **Or Run Step-by-Step**: 
   - Use `Shift + Enter` to run each cell
   - Interact with widgets as they appear

### Option 2: Google Colab (Cloud-based, No Installation)

#### Step 1: Upload to Colab
1. Go to [Google Colab](https://colab.research.google.com)
2. Click `File` → `Upload notebook`
3. Upload `warehouse_demo.ipynb`

#### Step 2: Install Dependencies in Colab
Uncomment the first cell in the notebook:
```python
!pip install plotly numpy pandas matplotlib scikit-learn pydeck geopandas shapely ipywidgets networkx pydantic --quiet
```

#### Step 3: Run the Notebook
Run cells sequentially using `Shift + Enter` or `Runtime` → `Run all`

### Option 3: VS Code with Jupyter Extension

#### Step 1: Install VS Code Extensions
- Install "Jupyter" extension by Microsoft
- Install "Python" extension by Microsoft

#### Step 2: Open the Notebook
```bash
# Open VS Code in the repository directory
code .

# Open the notebook file
# File → Open File → examples/warehouse_demo.ipynb
```

#### Step 3: Select Python Kernel
1. Click on the kernel selector in the top-right
2. Select your Python environment (with dependencies installed)

#### Step 4: Run Cells
Use the play button next to each cell or `Shift + Enter`

## 📋 Using the Interactive Widgets

### Step 1: Initialize System
Run the setup cells (Cells 1-4). This will:
- Import dependencies
- Initialize the WarehouseDigitalTwin system
- Set up global variables

### Step 2: Create Warehouse (Interactive)
You'll see widgets to configure your warehouse:

```
┌─────────────────────────────────────────┐
│ Name: [Mega Distribution Center______] │
│ Length (m): [200.0___]                  │
│ Width (m):  [150.0___]                  │
│ Height (m): [12.0____]                  │
│ Num Aisles: [10000___]                  │
│                                         │
│ [Create Warehouse]                      │
└─────────────────────────────────────────┘
```

**To use:**
1. Modify any values you want to change
2. Click the "Create Warehouse" button
3. View the warehouse statistics in the output area

**Example configurations:**
- **Small warehouse**: Length=50, Width=30, Aisles=100
- **Medium warehouse**: Length=100, Width=75, Aisles=1000
- **Large warehouse**: Length=200, Width=150, Aisles=10000
- **Mega warehouse**: Length=500, Width=300, Aisles=100000

### Step 3: Load Products (Interactive)
You'll see widgets to load or generate product data:

```
┌─────────────────────────────────────────┐
│ CSV Path: [test_data_unseen_expanded.csv] │
│                                         │
│ [Load from CSV] [Generate Sample Data] │
└─────────────────────────────────────────┘
```

**Option A - Load from CSV:**
1. Enter the path to your CSV file
   - Absolute path: `/full/path/to/file.csv`
   - Relative path: `data/my_products.csv`
2. Click "Load from CSV"
3. If file exists and is valid, products will be loaded
4. If file not found, you'll see a helpful error message

**Option B - Generate Sample Data:**
1. Click "Generate Sample Data"
2. System will create 5000 sample products automatically
3. Products will be displayed in the output area

**CSV Format Requirements:**
Your CSV should have these 23 columns:
- item_id, category, description, stock_level, reorder_point
- reorder_frequency_days, lead_time_days, daily_demand, demand_std_dev
- item_popularity_score, storage_location_id, zone, picking_time_seconds
- handling_cost_per_unit, unit_price, holding_cost_per_unit_day
- stockout_count_last_month, order_fulfillment_rate, total_orders_last_month
- turnover_ratio, layout_efficiency_score, last_restock_date
- forecasted_demand_next_7d, KPI_score

### Step 4: Continue with Analysis
After loading products, continue running cells sequentially:
- Train optimization model
- Optimize product allocation
- View utilization analysis
- Generate 3D visualizations
- Create geospatial maps
- Run AGV pathfinding simulations

## 🔧 Troubleshooting

### Issue: "Module not found" errors
**Solution:** Install missing dependencies
```bash
pip install -r requirements.txt
```

### Issue: "ipywidgets not displaying"
**Solution:** Enable Jupyter widgets extension
```bash
# For Jupyter Notebook
jupyter nbextension enable --py widgetsnbextension

# For JupyterLab 3.x
pip install jupyterlab_widgets

# For JupyterLab 2.x
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

### Issue: "FileNotFoundError" when loading CSV
**Solutions:**
1. **Check file path**: Ensure the path is correct (absolute or relative)
2. **Use absolute path**: `/full/path/to/your/file.csv`
3. **Use relative path from notebook**: `../data/file.csv`
4. **Alternative**: Click "Generate Sample Data" instead

### Issue: "No products loaded" error in training cell
**Solution:** 
1. Go back to the "Load Products" cell
2. Either load a CSV or generate sample data
3. Ensure you see "Successfully loaded X products" message
4. Then run the training cell again

### Issue: Widgets not responding
**Solution:**
1. Restart the kernel: `Kernel` → `Restart`
2. Run all cells again from the beginning
3. Ensure you're running cells in order

### Issue: Plots not displaying
**Solutions:**
```python
# Add this at the beginning if using Jupyter Notebook
%matplotlib inline

# For Plotly in JupyterLab, ensure you have the extension:
jupyter labextension install jupyterlab-plotly
```

## 💡 Tips and Best Practices

### Performance Tips
1. **Start small**: Test with fewer aisles (100-1000) first
2. **Scale up gradually**: Increase to 10,000+ once comfortable
3. **Limit visualizations**: Use `max_products` parameter for large datasets
4. **Generate sample data**: Faster than loading large CSV files

### Best Practices
1. **Run cells in order**: Don't skip cells
2. **Wait for completion**: Let each cell finish before running the next
3. **Check outputs**: Verify each step completed successfully
4. **Save frequently**: `File` → `Save and Checkpoint`
5. **Clear outputs before sharing**: `Cell` → `All Output` → `Clear`

### Common Workflows

#### Workflow 1: Quick Demo with Sample Data
```
1. Run setup cells (1-4)
2. Click "Create Warehouse" with default values
3. Click "Generate Sample Data"
4. Run remaining cells sequentially
```

#### Workflow 2: Custom Warehouse with Real Data
```
1. Run setup cells (1-4)
2. Modify warehouse parameters
3. Click "Create Warehouse"
4. Enter path to your CSV file
5. Click "Load from CSV"
6. Run remaining cells sequentially
```

#### Workflow 3: Experimentation
```
1. Run setup cells (1-4)
2. Try different warehouse sizes
3. Compare results with different product sets
4. Adjust parameters and re-run
```

## 📊 Sample Output

### Successful Warehouse Creation
```
🏗️ Creating warehouse: Mega Distribution Center
   Dimensions: 200m × 150m × 12m
   Aisles: 10000 (width: 3.0m)

📊 Warehouse Statistics:
   Total volume: 360,000 m³
   Estimated shelves: 120,000
   Storage systems: 10000
```

### Successful Product Loading
```
📁 Loading CSV: test_data_unseen_expanded.csv

✅ Successfully loaded 5000 products from CSV

   item_id  category  daily_demand  stock_level  ...
0  ITEM0001  electronics  45        320         ...
1  ITEM0002  groceries    78        450         ...
...
```

### Error: File Not Found
```
❌ Error: File not found: test_data_unseen_expanded.csv

Please check the file path and try again.
Or use 'Generate Sample Data' button to create test data.
```

## 🔗 Additional Resources

### Documentation
- [Main README](../README.md) - Project overview
- [Requirements](../requirements.txt) - Full dependency list

### Jupyter Resources
- [Jupyter Documentation](https://jupyter.org/documentation)
- [ipywidgets Documentation](https://ipywidgets.readthedocs.io/)
- [Google Colab Guide](https://colab.research.google.com/notebooks/intro.ipynb)

### Getting Help
- Check the [GitHub Issues](https://github.com/spacebeige/3d_mapping/issues)
- Review error messages carefully
- Try the "Generate Sample Data" option if CSV loading fails

## 📝 Example Commands Summary

```bash
# Full setup and run (local)
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping
pip install -r requirements.txt
jupyter notebook examples/warehouse_demo.ipynb

# Quick run if already set up
cd 3d_mapping
jupyter notebook examples/warehouse_demo.ipynb

# Run with JupyterLab
jupyter lab examples/warehouse_demo.ipynb

# Run with VS Code
code .
# Then open examples/warehouse_demo.ipynb
```

## ✅ Verification Checklist

Before running the notebook, ensure:
- [ ] Python 3.9+ is installed
- [ ] All dependencies are installed (`pip install -r requirements.txt`)
- [ ] Jupyter is installed and working
- [ ] You're in the correct directory
- [ ] (Optional) Your CSV file exists and has correct format

After running setup cells, verify:
- [ ] No error messages
- [ ] "✅ Setup complete!" message appears
- [ ] Widgets are displayed correctly
- [ ] Buttons are clickable

## 🎯 Success Criteria

You'll know everything is working when:
1. ✅ Widgets appear and are interactive
2. ✅ Warehouse creation shows statistics
3. ✅ Products load successfully (CSV or generated)
4. ✅ Visualizations render correctly
5. ✅ No error messages in any cell

---

## 🆕 Interactive Warehouse Builder (`interactive_warehouse.ipynb`)

### What's Special About This Notebook?

This notebook provides a **guided, step-by-step experience** that:
1. **Asks for warehouse dimensions** - Prompts you for length, width, height, aisles
2. **Adds products individually** - Enter each product one at a time
3. **Assigns unique positions automatically** - Each product gets a unique (x, y, z) position
4. **Shows individual products** - Each product displayed with its unique ID
5. **No coding required** - Just answer the prompts!

### How to Use

#### Step 1: Run the Setup Cell
```python
# Imports and setup - just run this cell
```

#### Step 2: Enter Warehouse Dimensions
You'll be prompted for:
```
Enter warehouse name (default: My Distribution Center): [Your Input]
Enter warehouse length in meters (default: 100): [Your Input]
Enter warehouse width in meters (default: 80): [Your Input]
Enter warehouse height in meters (default: 10): [Your Input]
Enter number of aisles (default: 10): [Your Input]
```

**Example:**
```
Enter warehouse name: My Warehouse
Enter warehouse length in meters: 150
Enter warehouse width in meters: 100
Enter warehouse height in meters: 12
Enter number of aisles: 20
```

#### Step 3: Add Products
For each product, you'll be prompted:
```
Product ID (default: PROD0001, or 'done' to finish): [Your Input]
Category (electronics/groceries/pharma/apparel/automotive): [Your Input]
Description: [Your Input]
Stock level (default: 100): [Your Input]
Daily demand (default: 10): [Your Input]
```

**Example Product 1:**
```
Product ID: LAPTOP001
Category: electronics
Description: Dell Laptop
Stock level: 50
Daily demand: 5

✅ Product added!
   ID: LAPTOP001
   Position: (12.50, 15.00, 2.40)
   Zone: C
```

**Example Product 2:**
```
Product ID: PHONE001
Category: electronics
Description: iPhone 15
Stock level: 200
Daily demand: 80

✅ Product added!
   ID: PHONE001
   Position: (25.00, 15.00, 2.40)
   Zone: A
```

Type `done` when finished adding products, or answer `n` when asked "Add another product?"

#### Step 4: View Summary
A table will display all your products with their:
- Product ID
- Category
- Description
- Stock Level
- Daily Demand
- Zone Assignment (A/B/C/D)
- Unique Position (X, Y, Z coordinates)

#### Step 5: Generate 3D Visualization
The notebook automatically creates a 3D visualization showing:
- Your warehouse structure (aisles, racks, shelves)
- Each product at its unique position
- Color-coded by zone
- Hover to see product details

#### Step 6: Download Files
The notebook saves:
- `warehouse_3d.html` - 3D visualization
- `products.csv` - Product data table
- `dashboard.html` - Analytics dashboard

### Key Features

**Automatic Position Assignment:**
Products are distributed evenly across:
- Multiple aisles (based on product count)
- Multiple racks (20 racks per aisle)
- Multiple shelves (5 shelves per rack)

**Smart Zone Assignment:**
- **Zone A**: High demand (>50 units/day) - Closest to exits
- **Zone B**: Medium demand (20-50 units/day)
- **Zone C**: Normal demand (10-20 units/day)
- **Zone D**: Low demand (<10 units/day) - Long-term storage

**Unique Product IDs:**
Each product gets:
- A unique identifier (e.g., PROD0001, PROD0002, or your custom ID)
- A unique 3D position (x, y, z coordinates)
- Never overlapping with other products

### Example Session

```
🏗️ WAREHOUSE CONFIGURATION
==================================================
Enter warehouse name: Tech Distribution Center
Enter warehouse length in meters: 120
Enter warehouse width in meters: 80
Enter warehouse height in meters: 10
Enter number of aisles: 15

📊 Warehouse Configuration:
   Name: Tech Distribution Center
   Dimensions: 120m × 80m × 10m
   Aisles: 15
   Volume: 96,000 m³

🏗️ Creating warehouse...
✅ Warehouse created successfully!

📦 PRODUCT INPUT
==================================================
Enter product details. Type 'done' when finished.

--- Product #1 ---
Product ID: LAPTOP-HP
Category: electronics
Description: HP Laptop 15-inch
Stock level: 80
Daily demand: 15

✅ Product added!
   ID: LAPTOP-HP
   Position: (5.33, 3.00, 2.00)
   Zone: C

Add another product? (y/n): y

--- Product #2 ---
Product ID: LAPTOP-DELL
Category: electronics
Description: Dell XPS 13
Stock level: 60
Daily demand: 25

✅ Product added!
   ID: LAPTOP-DELL
   Position: (10.67, 3.00, 2.00)
   Zone: B

Add another product? (y/n): n

✅ Total products added: 2

📋 PRODUCT SUMMARY
... [table displayed] ...

🎨 Generating 3D warehouse visualization...
✅ Visualization generated!

💾 Saving files...
✅ Saved: warehouse_3d.html
✅ Saved: products.csv
✅ Saved: dashboard.html
```

### Troubleshooting

**Q: The notebook doesn't prompt for input**
A: Make sure you're running in an interactive environment (Jupyter Notebook, not JupyterLab without proper extensions)

**Q: Can I add products in batch instead of one by one?**
A: Yes! Use the `warehouse_demo.ipynb` notebook instead, which supports CSV upload

**Q: The positions overlap**
A: The algorithm prevents overlaps by distributing products across different aisles, racks, and shelves based on their index

**Q: Can I customize the position assignment?**
A: Yes, you can modify the `assign_position()` function in the notebook

### Command-Line Alternative

If you prefer command-line interaction, use the Python script:

```bash
python interactive_warehouse.py
```

This provides the same functionality without needing Jupyter.

Happy building! 🚀
