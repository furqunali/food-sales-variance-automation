# Field → Source → Excel-Cell Map  (the automation "recipe")

This is the master mapping that drives the whole monthly automation. Every number in
the report has exactly one source file and one destination cell. Rows shift by month
(Jan = base row, add +1 per month: Aug = base+7).

**Store tabs (sample):** `1001` Cedar Crossing · `1002` Maple Junction · `1003` Harbor Point · `1004` Prairie Gate
**Month row offset:** Jan=0 … Jul=6 … **Aug=7** … Dec=11

## 1. Food Margin block  (Jan row = 6)  → e.g. August = row 13
| Report field | Cell (col) | Source file | Source location |
|---|---|---|---|
| GP % Before Discount | C | Weighted Average `.xlsx` | Comparison tab, col **G** (store row) |
| Discount % of Sales | D | Weighted Average | Comparison tab, col **I** |
| Discount $ Total | E | Weighted Average | Comparison tab, col **F** |
| Wastage $ | G | Cost INIR PDF | Kitchen **dept-24 Total → Waste** |
| Sampling $ (Free Food) | I | Cost INIR PDF | Kitchen dept-24 Total → **FreeFd** |
| Spoilage $ | K | Cost INIR PDF | Kitchen dept-24 Total → **Spoilage** |
| Logo-Cups Adjustment $ | M | Cost INIR PDF | Kitchen dept-24 Total → **Adjs** |
| INIR Net Margin | P | Weighted Average | Comparison tab, col **J** (= Cost INIR kitchen "Gross Margin %") |
| SOS Avg (numerator ÷ 60) | S | Speed of Service `.png` | Total row **"AVG Total Time (sec.)"** |
| *(F,H,J,L,N,O,Q,R are formulas — do not touch)* | | | |

## 2. Sales Budget vs Actual block  (Jan row = 20) → August = row 27
| Report field | Cell | Source | Location |
|---|---|---|---|
| C-Store Retail Actual | D | Retail Dept Summary PDF | site **Total Sales** |
| Kitchen Sales Actual | G | Weighted Average | Comparison tab col **D** (Sales $) |
| Inventory Shrink $ – Kitchen | L | Cost INIR PDF | Kitchen dept-24 Total **Variance Amount** |
| C-Store Inventory Shrink $ | N | Retail Dept Summary PDF | site **Audit-Adjs** total |
| Fountain Sales Actual | Q | Cost INIR PDF | Fountain dept-22 Total **"(Sales x)"** |
| Fountain Inventory Over/Short | S | Cost INIR PDF | Fountain dept-22 Total **Variance Amount** |
| Fountain INIR Net Margin | T | Cost INIR PDF | Fountain dept-22 **"Gross Margin %"** |
| *(C,F,I,P budgets are fixed; E,H,J,K,M,O,R formulas)* | | | |

## 3. Customer Counts block  (Jan row = 35) → August = row 42
| Report field | Cell | Source | Location |
|---|---|---|---|
| Total Customer # | C | Customer counts `.jpg` | "Customer #" |
| Crind | D | Customer counts `.jpg` | "Crind / Cimd SLS" |
| DR MOP | E | Customer counts `.jpg` | "DR MOP" |
| *(F,G,H,I,J formulas; J = days in month)* | | | |

## 4. Kitchen Sales breakdown  (Jan row = 50 or 51 depending on tab layout) → +7 for Aug
| Report field | Cols C..J | Source | Location |
|---|---|---|---|
| Hot Grab, Cold Grab, Bakery, MTO Food, MTO Coffee & Bev, Delivery, Catering, Midax | C–J | Hourly Sales Report `.xlsx` | LSK / kitchen category rows |

## 5. Ending Inventory (current-month snapshot — overwrite Q column)
| Dept (Cig/OT/Beer/Soda/Candy/Grocery/GM) | Q | Retail Dept Summary PDF | dept 1–7 **Ending-Inventory COST** column |
| Fountain | Q | Cost INIR PDF | Fountain Actual Ending |
| LSM (HOB) | Q | Cost INIR PDF | Kitchen Actual Ending |

## 6. Reports / Price Override (month column)
| Price Override Count | month col | Price Override `.xlsx` | that month's tab, site row → "Count of OVERRIDE PRICE" |

---
## Source-file read method (why an AI agent, not a plain script)
| Source | Format | Read by |
|---|---|---|
| Weighted Average, Hourly Sales, Price Override | `.xlsx` (structured) | openpyxl — exact |
| Retail Dept Summary | digital PDF (has text) | pdfplumber — exact |
| **Cost INIR** | **scanned image PDF (no text)** | **AI vision / OCR** |
| **Customer Counts** | **`.jpg` screenshot** | **AI vision** |
| **Speed of Service** | **`.png`** | **AI vision** |

## Verification rules (the "catch-mistakes" checks)
- **Ending Inventory (Q)** must equal Retail Dept Summary dept-cost column (this rule has caught wrong-column / wrong-store paste errors in practice).
- **Kitchen Shrink (L)** must equal Cost INIR kitchen dept-24 Variance (this rule has caught a stale/mistyped value in practice).
- **Total = C-Store + Kitchen** for every month.
- **MoM change** flag: store sales > ±15%, any margin/GP%/shrink > ±5 pts, override > ±50%.
