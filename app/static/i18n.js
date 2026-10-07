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
  wxSample: ["Sample weather (demo, not real)", "నమూనా వాతావరణం (డెమో, నిజం కాదు)"],
  actOpenPlan: ["Open plan", "ప్రణాళిక తెరువు"],
  wzLastWater: ["When did you last water it?", "చివరిసారి ఎప్పుడు నీరు పెట్టారు?"], wzLW1: ["Today or yesterday", "ఈరోజు లేదా నిన్న"], wzLW3: ["2-3 days ago", "2-3 రోజుల క్రితం"],
  wzLW6: ["4-7 days ago", "4-7 రోజుల క్రితం"], wzLW10: ["More than a week ago", "వారం కంటే ఎక్కువ రోజుల క్రితం"], wzLWn: ["Not sure", "తెలియదు"],
  dueOn: ["Due {d}", "గడువు {d}"], tToday: ["Today", "ఈరోజు"], tPlan: ["Plan", "ప్రణాళిక"],
  wxUpdated: ["Weather updated {t}", "వాతావరణం {t} నవీకరించబడింది"], agoNow: ["just now", "ఇప్పుడే"], agoMin: ["{n} min ago", "{n} నిమిషాల క్రితం"], agoHr: ["{n} h ago", "{n} గంటల క్రితం"],
  humidity: ["Humidity {h}%", "తేమ {h}%"], wind: ["Wind {w} km/h", "గాలి {w} కి.మీ/గం"], rainMm: ["{n} mm", "{n} మి.మీ"],
  noLocCard: ["Add your location for live weather and exact watering advice.", "ప్రత్యక్ష వాతావరణం, కచ్చితమైన నీటి సలహా కోసం మీ ప్రాంతం చేర్చండి."],
  setLoc: ["Set location", "ప్రాంతం నమోదు"], wxDown: ["Weather is not available right now.", "వాతావరణం ఇప్పుడు అందుబాటులో లేదు."],
  todayTitle: ["What to do today", "ఈరోజు చేయాల్సిన పనులు"], allDone: ["Nothing to do today ✓", "ఈరోజు చేయాల్సిన పని ఏదీ లేదు ✓"],
  showAll: ["Show all {n} tasks", "మొత్తం {n} పనులు చూపు"], showLess: ["Show less", "తక్కువ చూపు"],
  actWatered: ["Watered", "నీరు పెట్టాను"], actDone: ["Done", "అయింది"], actHarvested: ["Harvested", "కోశాను"], actSetDate: ["Set date", "తేదీ నమోదు"],
  actOk: ["OK", "సరే"], actLater: ["Later", "తర్వాత"], saved: ["Saved", "సేవ్ అయింది"], undo: ["Undo", "వెనక్కి"],
  myFarm: ["My crops today", "నా పంటలు ఈరోజు"], dayN: ["Day {n}", "రోజు {n}"], harvestAbout: ["Harvest from about {d}", "కోత సుమారు {d} నుంచి"],
  noDateYet: ["Planting date not set", "నాటిన తేదీ నమోదు కాలేదు"], setupFarm: ["Set up my farm (1 minute)", "నా పొలం సెటప్ చేయి (1 నిమిషం)"],
  stageLbl: ["Stage", "దశ"], edit: ["Edit", "మార్చు"], markHarvested: ["Mark as harvested", "కోత పూర్తయింది"],
  noPlot: ["No active plot for this crop yet.", "ఈ పంటకు ఇంకా చురుకైన పొలం లేదు."], addPlot: ["Add plot", "పొలం చేర్చు"],
  nextSteps: ["Next steps", "తదుపరి పనులు"], waterTitle: ["Watering", "నీటి పారుదల"], wateredToday: ["Watered today", "ఈరోజు నీరు పెట్టాను"],
  wateredOther: ["Watered on another day", "వేరే రోజు నీరు పెట్టాను"], waterCount: ["Watered {n} times · last {d}", "{n} సార్లు నీరు పెట్టారు · చివరిసారి {d}"],
  waterNever: ["Not watered yet", "ఇంకా నీరు పెట్టలేదు"], todayWord: ["today", "ఈరోజు"], daysAgoN: ["{n} days ago", "{n} రోజుల క్రితం"],
  deficit: ["Soil water deficit {d} of {t} mm", "నేలలో నీటి లోటు {d} / {t} మి.మీ"], deficitHelp: ["When the bar is full, water the crop.", "బార్ నిండినప్పుడు పంటకు నీరు పెట్టండి."],
  fertTitle: ["Fertilizer schedule", "ఎరువుల షెడ్యూల్"], stDone: ["Done {d}", "పూర్తి {d}"], stDue: ["Due now", "ఇప్పుడు వేయాలి"], stOverdue: ["Overdue", "ఆలస్యం"],
  stSoon: ["Soon", "త్వరలో"], stLater: ["Later", "తర్వాత"], stAssumed: ["Earlier step (assumed done)", "ముందు దశ (పూర్తయిందని భావిస్తున్నాం)"], stMissed: ["Skipped", "వదిలేసారు"],
  stagesTitle: ["Growth stages and key watering times", "పెరుగుదల దశలు, ముఖ్య నీటి సమయాలు"], keyWater: ["Key watering", "ముఖ్య నీటి సమయం"],
  tipsTitle: ["Good to know", "తెలుసుకోవాల్సినవి"],
  guideline: ["This plan is a general guideline and has not yet been reviewed by an agriculture officer. Confirm with your local KVK before acting, especially on fertilizer amounts.",
              "ఈ ప్రణాళిక సాధారణ మార్గదర్శకం మాత్రమే, వ్యవసాయ అధికారి ఇంకా పరిశీలించలేదు. ముఖ్యంగా ఎరువుల పరిమాణాల విషయంలో చర్య తీసుకునే ముందు స్థానిక KVKని సంప్రదించండి."],
  calcDetails: ["Custom fertilizer calculator (with soil test)", "ఎరువుల కాలిక్యులేటర్ (మట్టి పరీక్షతో)"],
  wzWelcome: ["Welcome! Let's set up your farm in about a minute.", "స్వాగతం! ఒక నిమిషంలో మీ పొలం సెటప్ చేద్దాం."], wzLang: ["Choose your language", "మీ భాష ఎంచుకోండి"],
  wzNext: ["Next", "తరువాత"], wzBack: ["Back", "వెనక్కి"], wzSkip: ["Skip for now", "ఇప్పుడు వద్దు"],
  wzPlace: ["Where is your farm?", "మీ పొలం ఎక్కడ?"], wzUseLoc: ["📍 Use my location", "📍 నా ప్రాంతం వాడు"], wzOrDistrict: ["or choose your district", "లేదా మీ జిల్లా ఎంచుకోండి"],
  wzLocOk: ["Location saved ✓", "ప్రాంతం సేవ్ అయింది ✓"], wzLocFail: ["Could not get your location. Please choose your district.", "మీ ప్రాంతం దొరకలేదు. దయచేసి మీ జిల్లా ఎంచుకోండి."],
  wzWhyLoc: ["Used only for live weather and watering advice.", "ప్రత్యక్ష వాతావరణం, నీటి సలహా కోసం మాత్రమే వాడతాం."], wzChoose: ["Choose district", "జిల్లా ఎంచుకోండి"],
  wzCrops: ["What do you grow? Tap all that apply.", "మీరు ఏ పంటలు పండిస్తారు? వర్తించేవన్నీ నొక్కండి."], wzPickOne: ["Pick at least one crop", "కనీసం ఒక పంట ఎంచుకోండి"],
  wzCropOf: ["Crop {i} of {n}", "పంట {i} / {n}"], wzAcres: ["How many acres of {crop}?", "{crop} ఎన్ని ఎకరాలు?"], wzWhen: ["When did you plant it?", "ఎప్పుడు నాటారు?"],
  wzNotYet: ["Not yet", "ఇంకా లేదు"], wzWeek: ["This week", "ఈ వారం"], wzWeeks: ["2-4 weeks ago", "2-4 వారాల క్రితం"], wzMonths: ["1-2 months ago", "1-2 నెలల క్రితం"], wzPick: ["Pick a date", "తేదీ ఎంచుకోండి"],
  wzApprox: ["About {d}. You can fix the exact date later.", "సుమారు {d}. సరైన తేదీని తర్వాత మార్చుకోవచ్చు."],
  wzWater: ["How do you water it?", "నీరు ఎలా పెడతారు?"], wzRain: ["Rain only", "వర్షం మాత్రమే"], wzBore: ["Borewell / well", "బోరు / బావి"], wzCanal: ["Canal / tank", "కాలువ / చెరువు"], wzDrip: ["Drip", "డ్రిప్"],
  wzDone: ["Your plan is ready", "మీ ప్రణాళిక సిద్ధం"], wzSummary: ["{n} crop(s), {a} acres. We will tell you what to do each day.", "{n} పంట(లు), {a} ఎకరాలు. ప్రతిరోజూ ఏం చేయాలో చెబుతాం."],
  wzOpen: ["Open my Today screen", "నా ఈరోజు స్క్రీన్ తెరువు"], wzSaving: ["Saving…", "సేవ్ అవుతోంది…"], wzErr: ["Could not save: {e}", "సేవ్ కాలేదు: {e}"],
  wzEdit: ["Edit {crop}", "{crop} మార్చు"], wzSave: ["Save", "సేవ్"], wzClose: ["Close", "మూసివేయి"],
  errPrefix: ["Error", "లోపం"],
  allCrops: ["All crops", "అన్ని పంటలు"], addCrop: ["Add crop", "పంట చేర్చు"], myCrops: ["My crops (tap to open)", "నా పంటలు (తెరవడానికి నొక్కండి)"],
  addCropTitle: ["Add a crop or plot", "పంట / పొలం చేర్చండి"], plots: ["Plots", "పొలాలు"],
  noCrops: ["No crops yet. Add your first crop below.", "ఇంకా పంటలు లేవు. మీ మొదటి పంటను క్రింద చేర్చండి."],
  noPlots: ["No plots recorded for this crop. Add one below so cost per acre works.", "ఈ పంటకు పొలాలు నమోదు కాలేదు. ఎకరాకు ఖర్చు రావడానికి క్రింద చేర్చండి."],
  wholeFarm: ["Whole farm", "మొత్తం పొలం"], acres: ["Area (acre)", "విస్తీర్ణం (ఎకరాలు)"], acreN: ["{a} acre", "{a} ఎకరాలు"],
  spentSoFar: ["Spent so far (no sales yet)", "ఇప్పటి వరకు ఖర్చు (అమ్మకాలు లేవు)"],
  priceNow: ["Price now", "ఇప్పటి ధర"], next14: ["14-day trend", "14 రోజుల ధోరణి"],
  sown: ["Sown {d} ({n} days ago)", "విత్తింది {d} ({n} రోజుల క్రితం)"], notSown: ["Sowing date not set", "విత్తిన తేదీ నమోదు కాలేదు"],
  useMarket: ["Use today's market price: ₹{price}", "నేటి మార్కెట్ ధర వాడండి: ₹{price}"],
  cropCol: ["Crop", "పంట"], lastAct: ["Last entry {d}", "చివరి నమోదు {d}"],
  tSum: ["Summary", "సారాంశం"], tProfit: ["Profit", "లాభం"], tPrices: ["Prices", "ధరలు"], tMoney: ["Expenses", "ఖర్చులు"], tFert: ["Fertilizer", "ఎరువు"],
  noSales: ["No sales yet", "అమ్మకాలు లేవు"], mExp: ["Add expense", "ఖర్చు నమోదు"], mSale: ["Record sale", "అమ్మకం నమోదు"],
  recent: ["Recent entries", "ఇటీవలి నమోదులు"], kind: ["Type", "రకం"], kExp: ["Expense", "ఖర్చు"], kSale: ["Sale", "అమ్మకం"],
  swipeHint: ["Swipe left or right to change crop", "పంట మార్చడానికి ఎడమ లేదా కుడివైపు స్వైప్ చేయండి"],
  prevCrop: ["Previous crop", "ముందరి పంట"], nextCrop: ["Next crop", "తరువాతి పంట"],
  demoMix: ["DEMO prices (not real)", "డెమో ధరలు (నిజమైనవి కావు)"],
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
const CROP_EM = {chilli:"🌶️",onion:"🧅",tomato:"🍅",paddy:"🍚",wheat:"🌾",cotton:"☁️",maize:"🌽",groundnut:"🥜",turmeric:"🌱"};
const cropEm = k => CROP_EM[k] || "🌿";
// two-line label (Telugu over English) when "both" is selected, single line otherwise
const lines = (en, te) => LANG === "en" ? en : LANG === "te" ? te : te + "\n" + en;
const cropLines = k => lines(k, CROPS_TE[k] || k);
const catName = k => join(k, CATS_TE[k] || k);
// server messages carry text (English) and text_te
function pick(m) { return LANG === "en" ? m.text : LANG === "te" ? m.text_te : m.text_te + "\n" + m.text; }
