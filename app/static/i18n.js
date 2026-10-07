// UI strings: [English, Telugu]. Telugu wording should be reviewed by a native speaker.
const STR = {
  title: ["Farmer Dashboard", "రైతు డాష్‌బోర్డ్"],
  crop: ["Crop", "పంట"],
  refresh: ["Refresh live prices", "తాజా ధరలు తెచ్చుకో"],
  demo: ["DEMO data (not real prices)", "డెమో డేటా (నిజమైన ధరలు కావు)"],
  live: ["LIVE Agmarknet prices", "ప్రత్యక్ష అగ్‌మార్క్‌నెట్ ధరలు"],
  totalCost: ["Total cost", "మొత్తం ఖర్చు"], revenue: ["Revenue", "ఆదాయం"], profit: ["Profit", "లాభం"],
  costAcre: ["Cost / acre", "ఎకరాకు ఖర్చు"], costQ: ["Cost / quintal", "క్వింటాల్‌కు ఖర్చు"],
  avgSale: ["Avg sale price", "సగటు అమ్మకం ధర"], mktNow: ["Market price now", "ఇప్పటి మార్కెట్ ధర"],
  priceChart: ["Price (Rs/quintal) and 14-day forecast", "ధర (₹/క్వింటాల్) మరియు 14 రోజుల అంచనా"],
  actual: ["Actual", "నిజమైన"], forecast: ["Forecast", "అంచనా"],
  fcNote: ["Damped-trend smoothing on past prices only. Expected change {ch}%; last-week error {mape}%. The band is a rough 95% range.",
           "గత ధరల ఆధారంగా మాత్రమే అంచనా. అంచనా మార్పు {ch}%; గత వారం తప్పిదం {mape}%. బ్యాండ్ సుమారు 95% పరిధి."],
  sell: ["Sell / hold advice", "అమ్మాలా / ఆపాలా సలహా"], costIns: ["Cost insights", "ఖర్చుల సూచనలు"],
  byCat: ["Expenses by category", "విభాగాల వారీగా ఖర్చులు"], byMonth: ["Monthly expenses", "నెలవారీ ఖర్చులు"],
  markets: ["Today's market prices (best first)", "నేటి మార్కెట్ ధరలు (ఎక్కువ ముందు)"],
  state: ["State", "రాష్ట్రం"], market: ["Market", "మార్కెట్"], modal: ["Modal", "సాధారణ ధర"], min: ["Min", "కనిష్ఠ"], max: ["Max", "గరిష్ఠ"],
  addExp: ["Add expense", "ఖర్చు నమోదు"], addSale: ["Record sale", "అమ్మకం నమోదు"], addPlot: ["Add plot", "పొలం నమోదు"],
  date: ["Date", "తేదీ"], category: ["Category", "విభాగం"], amount: ["Amount (₹)", "మొత్తం (₹)"], note: ["Note", "గమనిక"],
  qty: ["Quintals", "క్వింటాళ్లు"], pricePerQ: ["₹ per quintal", "క్వింటాల్‌కు ₹"], area: ["Area (acre)", "విస్తీర్ణం (ఎకరాలు)"],
  sowing: ["Sowing date", "విత్తిన తేదీ"], save: ["Save", "సేవ్ చేయి"],
  fert: ["Fertilizer calculator", "ఎరువుల కాలిక్యులేటర్"], soilN: ["Soil N kg/ha", "మట్టి N కి.గ్రా/హె."],
  soilP: ["Soil P kg/ha", "మట్టి P కి.గ్రా/హె."], soilK: ["Soil K kg/ha", "మట్టి K కి.గ్రా/హె."], ph: ["Soil pH", "మట్టి pH"],
  getPlan: ["Get plan", "ప్రణాళిక చూపు"],
  soilRatings: ["Soil rating N/P/K: {v}", "మట్టి స్థాయి N/P/K: {v}"],
  nutrients: ["Nutrients needed (kg): N {n}, P2O5 {p}, K2O {k}", "కావలసిన పోషకాలు (కి.గ్రా): N {n}, P2O5 {p}, K2O {k}"],
  products: ["Fertilizer: DAP {dap} kg, Urea {urea} kg, MOP {mop} kg", "ఎరువులు: DAP {dap} కి.గ్రా, యూరియా {urea} కి.గ్రా, MOP {mop} కి.గ్రా"],
  low: ["low", "తక్కువ"], medium: ["medium", "మధ్యస్థం"], high: ["high", "ఎక్కువ"],
  recentExp: ["Recent expenses", "ఇటీవలి ఖర్చులు"], recentSales: ["Recent sales", "ఇటీవలి అమ్మకాలు"],
  qtyShort: ["Qty (q)", "పరిమాణం (క్వి.)"], rsQ: ["₹/q", "₹/క్వి."], del: ["Delete", "తొలగించు"],
  // profit calculator
  calcTitle: ["{crop} profit calculator", "{crop} లాభం లెక్క"],
  moneyOut: ["Your money out", "మీ ఖర్చులు"], invested: ["Money invested per acre (₹)", "ఎకరాకు పెట్టుబడి (₹)"],
  yieldQ: ["Yield (quintals per acre)", "దిగుబడి (ఎకరాకు క్వింటాళ్లు)"],
  other: ["Transport and other charges (₹ per quintal)", "రవాణా, ఇతర ఖర్చులు (క్వింటాల్‌కు ₹)"],
  sellPrice: ["Your selling price", "మీ అమ్మకం ధర"], sellPriceIn: ["Selling price (₹ per quintal)", "అమ్మే ధర (క్వింటాల్‌కు ₹)"],
  useMsp: ["Use MSP {season}: ₹{price}", "కనీస మద్దతు ధర (MSP) {season} వాడండి: ₹{price}"],
  resProfit: ["Profit", "లాభం"], resLoss: ["Loss", "నష్టం"], resSmall: ["Small profit (under 15%)", "తక్కువ లాభం (15% లోపు)"],
  perAcre: ["Profit per acre", "ఎకరాకు లాభం"], perQuintal: ["Profit per quintal", "క్వింటాల్‌కు లాభం"],
  roi: ["Return on money invested", "పెట్టుబడిపై రాబడి"], breakEven: ["Break-even price", "నష్టం రాని కనీస ధర"],
  targetTitle: ["Price needed for a target profit", "కావలసిన లాభానికి అవసరమైన ధర"],
  targetIn: ["Target profit per acre (₹)", "ఎకరాకు కావలసిన లాభం (₹)"], sellAtLeast: ["Sell at least at", "కనీసం ఈ ధరకు అమ్మండి"],
  atPrices: ["Profit at different prices", "వివిధ ధరల వద్ద లాభం"],
  priceQ: ["Price per quintal", "క్వింటాల్ ధర"], yours: ["yours", "మీది"],
  mspNote: ["MSP is the government's minimum price; the market price can be higher or lower. Investment, yield and the 15% line are your own assumptions.",
            "MSP అంటే ప్రభుత్వ కనీస మద్దతు ధర; మార్కెట్ ధర ఎక్కువ లేదా తక్కువ ఉండవచ్చు. పెట్టుబడి, దిగుబడి, 15% అనేవి మీ అంచనాలు."],
  fillCalc: ["Enter investment, yield and price to see profit.", "లాభం చూడటానికి పెట్టుబడి, దిగుబడి, ధర నమోదు చేయండి."],
  errPrefix: ["Error", "లోపం"],
};
const CROPS_TE = {chilli:"మిర్చి",onion:"ఉల్లి",tomato:"టమాటా",paddy:"వరి",wheat:"గోధుమ",cotton:"పత్తి",maize:"మొక్కజొన్న",groundnut:"వేరుశనగ",turmeric:"పసుపు"};
const CATS_TE = {seed:"విత్తనాలు",fertilizer:"ఎరువులు",pesticide:"పురుగుమందులు",labour:"కూలీ",irrigation:"నీటిపారుదల",machinery:"యంత్రాలు",transport:"రవాణా",other:"ఇతరాలు"};

let LANG = "both"; try { LANG = localStorage.getItem("lang") || "both"; } catch {}
function setLang(l) { LANG = l; try { localStorage.setItem("lang", l); } catch {} }
function join(en, te) { return LANG === "en" ? en : LANG === "te" ? te : te + " · " + en; }
function L(key, vars) {
  const [en, te] = STR[key]; let a = en, b = te;
  for (const k in vars || {}) {
    const v = vars[k];  // crop is passed as a raw key and named per language
    a = a.replaceAll("{" + k + "}", v); b = b.replaceAll("{" + k + "}", k === "crop" ? (CROPS_TE[v] || v) : v);
  }
  return join(a, b);
}
const cropName = k => join(k, CROPS_TE[k] || k);
const catName = k => join(k, CATS_TE[k] || k);
// server messages carry text (English) and text_te
function pick(m) { return LANG === "en" ? m.text : LANG === "te" ? m.text_te : m.text_te + "\n" + m.text; }
