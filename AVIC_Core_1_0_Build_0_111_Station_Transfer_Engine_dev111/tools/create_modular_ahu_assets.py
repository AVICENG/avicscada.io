from pathlib import Path
import re, json, hashlib
import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
SVG_DIR=ROOT/'avic_core/ui/static/svg-library'
SVG_DIR.mkdir(parents=True, exist_ok=True)

STYLE='''
<style>
  .ahu-metal{fill:url(#__PFX__metal);stroke:#52616f;stroke-width:2.1;stroke-linejoin:round}
  .ahu-metal-light{fill:url(#__PFX__light);stroke:#71808d;stroke-width:1.25;stroke-linejoin:round}
  .ahu-metal-dark{fill:url(#__PFX__dark);stroke:#43515d;stroke-width:1.4;stroke-linejoin:round}
  .ahu-interior{fill:url(#__PFX__interior);stroke:#6c7b87;stroke-width:1.3}
  .ahu-edge{fill:none;stroke:#dce3e8;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
  .ahu-seam{fill:none;stroke:#687784;stroke-width:1.2}
  .ahu-bolt{fill:#d9e0e5;stroke:#5e6d79;stroke-width:.8}
  .ahu-air{fill:none;stroke:#55b6ec;stroke-width:4;stroke-linecap:round;stroke-linejoin:round;opacity:0}
  .ahu-air-dash{fill:none;stroke:#e0f5ff;stroke-width:2.3;stroke-linecap:round;stroke-dasharray:8 13;opacity:0}
  .ahu-particle{fill:#8bdbff;opacity:0}
  .ahu-flow-label{font-family:Arial,sans-serif;font-size:8px;fill:#4a9bca;opacity:.0}
  .ahu-blade{fill:url(#__PFX__blade);stroke:#536575;stroke-width:1.25;stroke-linejoin:round}
  .ahu-fin{stroke:#aab8c4;stroke-width:1.1;opacity:.95}
  .ahu-copper{fill:none;stroke:#d47c43;stroke-width:5;stroke-linecap:round;stroke-linejoin:round}
  .ahu-hot{fill:none;stroke:#ed694b;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
  .ahu-cold{fill:none;stroke:#278bd4;stroke-width:4;stroke-linecap:round;stroke-linejoin:round}
  .damper-blades{transform-box:fill-box;transform-origin:center;transform:rotate(0deg);transition:transform .65s cubic-bezier(.2,.8,.2,1)}
  .state-damper-open .damper-blades{transform:rotate(68deg)}
  .fan-rotor{transform-box:view-box;transform-origin:206px 143px}
  @keyframes avicFanSpin{to{transform:rotate(360deg)}}
  .state-fan-running .fan-rotor{animation:avicFanSpin .72s linear infinite}
  .ahu-air-system .ahu-air,.ahu-air-system .ahu-air-dash{opacity:0}
  .state-airflow .ahu-air{opacity:.95}
  .state-airflow .ahu-air-dash{opacity:.9;animation:avicAirFlow 1.05s linear infinite}
  .state-airflow .ahu-particle{opacity:.9;animation:avicParticle 2.3s linear infinite}
  @keyframes avicAirFlow{to{stroke-dashoffset:-42}}
  @keyframes avicParticle{from{transform:translateX(0);opacity:0}12%{opacity:.9}88%{opacity:.9}to{transform:translateX(295px);opacity:0}}
  @media(prefers-reduced-motion:reduce){.state-fan-running .fan-rotor,.state-airflow .ahu-air-dash,.state-airflow .ahu-particle{animation:none!important}.damper-blades{transition:none!important}}
</style>'''

# Shared cabinet casing: identical envelope and mating rings for all 7 modules.
def chassis(pfx, *, open_outlet=False):
    # cabinet face is intentionally cut away: the internal section is visible.
    side = '' if open_outlet else f'''<path class="ahu-metal-dark" d="M302 66 352 92 352 207 302 181Z"/>
      <path d="M310 83 340 99 340 190 310 174Z" fill="#202b35" opacity=".42"/>'''
    outlet_frame = '''<path d="M302 66 352 92 352 207 302 181" fill="none" stroke="#71808d" stroke-width="4"/>''' if open_outlet else '''<path d="M302 66 352 92 352 207 302 181" fill="none" stroke="#71808d" stroke-width="3"/>'''
    # common viewBox 0 0 400 320 for all section assets; equipment occupies same cutaway aperture.
    return f'''
  <defs>
    <linearGradient id="{pfx}metal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f4f7f9"/><stop offset=".28" stop-color="#b8c2cb"/><stop offset=".56" stop-color="#e4e9ed"/><stop offset="1" stop-color="#87939e"/></linearGradient>
    <linearGradient id="{pfx}light" x1="0" y1="0" x2=".15" y2="1"><stop offset="0" stop-color="#f7f9fa"/><stop offset=".5" stop-color="#c6d0d8"/><stop offset="1" stop-color="#8e9ba7"/></linearGradient>
    <linearGradient id="{pfx}dark" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#75828d"/><stop offset="1" stop-color="#394652"/></linearGradient>
    <linearGradient id="{pfx}interior" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#34414c"/><stop offset="1" stop-color="#111b24"/></linearGradient>
    <linearGradient id="{pfx}blade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1f4f6"/><stop offset=".45" stop-color="#aebbc5"/><stop offset="1" stop-color="#687885"/></linearGradient>
    <filter id="{pfx}shadow" x="-20%" y="-25%" width="140%" height="160%"><feGaussianBlur stdDeviation="7"/></filter>
    <marker id="{pfx}arrow" markerWidth="7" markerHeight="7" refX="5.6" refY="3.5" orient="auto"><path d="M0 0 7 3.5 0 7Z" fill="#55b6ec"/></marker>
  </defs>
  <ellipse cx="198" cy="250" rx="162" ry="18" fill="#263746" opacity=".17" filter="url(#{pfx}shadow)"/>
  <!-- lower skid and support feet -->
  <path d="M35 205 302 205 353 232 86 232Z" class="ahu-metal-dark"/>
  <path d="M52 218 62 218 62 244 52 244ZM118 224 128 224 128 246 118 246ZM289 224 299 224 299 246 289 246ZM333 218 343 218 343 242 333 242Z" class="ahu-metal"/>
  <path d="M35 205 302 205 353 232 86 232" class="ahu-edge"/>
  <!-- roof and rear casing -->
  <path d="M35 70 302 70 352 96 85 96Z" class="ahu-metal"/>
  <path d="M35 70 85 96 85 205 35 179Z" class="ahu-metal-dark"/>
  <path d="M85 96 352 96 352 207 85 207Z" class="ahu-interior"/>
  {side}
  <!-- upper and lower longitudinal rails, left/right mating flanges are identical -->
  <path d="M35 70 302 70 352 96 85 96" fill="none" stroke="#eef2f5" stroke-width="4"/>
  <path d="M35 179 302 179 352 207 85 207" fill="none" stroke="#687783" stroke-width="5"/>
  <path d="M42 62 310 62 361 89 93 89Z" class="ahu-metal-light"/>
  <path d="M42 62 93 89 93 198 42 171Z" fill="none" stroke="#72808c" stroke-width="4"/>
  {outlet_frame}
  <!-- repeated coupling flanges and bolts -->
  <path d="M82 91 91 96 91 208 82 203Z" fill="#d9e0e5" stroke="#687784" stroke-width="1.3"/>
  <path d="M294 91 303 96 303 208 294 203Z" fill="#aab5be" stroke="#667581" stroke-width="1.3"/>
  {''.join(f'<circle class="ahu-bolt" cx="{x}" cy="{y}" r="2.1"/>' for x in (86,298) for y in (103,126,151,181,198))}
  <!-- open cutaway rim; no solid front side wall hides the equipment -->
  <path d="M92 103 292 103M92 191 292 191" fill="none" stroke="#c3cdd5" stroke-width="3"/>
  <path d="M92 103 92 191M292 103 292 191" fill="none" stroke="#82909b" stroke-width="3"/>
'''

# Each internal feature is custom vector art in the same exact chamber coordinates.
modules={}
modules['ahu_section_outdoor_damper'] = {
 'name':'ПВУ · Секция заслонки наружного воздуха','category':'ПВУ · модульные секции','description':'Объёмная секция наружного воздуха с многолопаточной заслонкой и электроприводом. Лопатки открываются по Boolean/feedback=1.','tags':'пву приточная установка наружный воздух заслонка привод damper модуль animated airflow','body':'''<g>
  <path d="M111 112 158 112 158 178 111 178Z" fill="#182631" stroke="#92a0ab" stroke-width="2"/>
  <path d="M116 115 153 115 153 175 116 175Z" fill="#283640"/>
  <g class="damper-blades">
    <g class="damper-blade"><path d="M117 119 153 119 148 126 117 126Z" class="ahu-blade"/><path d="M118 120 148 120" stroke="#f6f8fa" stroke-width="1"/></g>
    <g class="damper-blade"><path d="M117 133 153 133 148 140 117 140Z" class="ahu-blade"/><path d="M118 134 148 134" stroke="#f6f8fa" stroke-width="1"/></g>
    <g class="damper-blade"><path d="M117 147 153 147 148 154 117 154Z" class="ahu-blade"/><path d="M118 148 148 148" stroke="#f6f8fa" stroke-width="1"/></g>
    <g class="damper-blade"><path d="M117 161 153 161 148 168 117 168Z" class="ahu-blade"/><path d="M118 162 148 162" stroke="#f6f8fa" stroke-width="1"/></g>
  </g>
  <path d="M153 118 174 108 174 172 153 180Z" fill="#667783" opacity=".55"/>
  <path d="M132 113 132 101 151 91 169 99 169 111" class="ahu-metal-light"/>
  <rect x="145" y="82" width="31" height="19" rx="3" fill="#e87934" stroke="#7d4a2d" stroke-width="1.4"/>
  <rect x="151" y="86" width="18" height="11" rx="2" fill="#f5a05d"/>
  <circle cx="160" cy="91.5" r="2.5" fill="#39434b"/>
  <path d="M160 101 160 112 154 118" fill="none" stroke="#424e58" stroke-width="3"/>
  <path d="M182 108 182 178" stroke="#aebbc4" stroke-width="2"/>
</g>'''
}
modules['ahu_section_filter']={
 'name':'ПВУ · Секция фильтров','category':'ПВУ · модульные секции','description':'Секция карманных фильтров с выдвижной рамой и прижимами.','tags':'пву фильтр карманный кассетный очистка воздуха filter модуль','body':'''<g>
  <path d="M111 108 268 108 268 181 111 181Z" fill="#1b2833" stroke="#8f9ca7" stroke-width="2"/>
  <path d="M118 113 258 113 258 176 118 176Z" fill="#d7e0e6" stroke="#667784" stroke-width="2"/>
  {FILTER_BAGS}
  <path d="M110 106 268 106" stroke="#f3f6f8" stroke-width="3"/>
  <path d="M110 181 268 181" stroke="#687783" stroke-width="4"/>
  <path d="M260 112 270 117 270 174 260 179" fill="none" stroke="#657480" stroke-width="2"/>
</g>'''.replace('{FILTER_BAGS}', ''.join(
  f'<path d="M{120+i*34} 116 L{145+i*34} 116 L{145+i*34} 171 L{120+i*34} 171Z" fill="#eef2f4" stroke="#8b99a5" stroke-width="1.3"/><path d="M{122+i*34} 118 L{127+i*34} 168 M{128+i*34} 118 L{133+i*34} 168 M{134+i*34} 118 L{139+i*34} 168" stroke="#bec9d1" stroke-width="1.2"/> '
  for i in range(4)))
}
modules['ahu_section_heat_recovery']={
 'name':'ПВУ · Секция рекуператора','category':'ПВУ · модульные секции','description':'Пластинчатый перекрёстноточный рекуператор в общей раме; встречные воздушные каналы показаны синим и оранжевым.','tags':'пву рекуператор пластинчатый теплоутилизация heat recovery модуль','body':'''<g>
  <path d="M116 111 250 111 276 126 142 126Z" fill="#b7c2ca" stroke="#667784" stroke-width="1.5"/>
  <path d="M142 126 276 126 276 177 142 177Z" fill="#7c8b96" stroke="#4f5f6b" stroke-width="1.5"/>
  <path d="M116 111 142 126 142 177 116 162Z" fill="#566571" stroke="#b5c0c9" stroke-width="1.5"/>
  <path d="M128 116 255 116 267 123 140 123Z" fill="#e3e8ec" opacity=".9"/>
  {RECUP_PLATES}
  <path d="M111 105 252 105 282 123 282 182 142 182 111 164Z" fill="none" stroke="#d0d9df" stroke-width="2.5"/>
  <path d="M122 130 137 139" stroke="#e57d48" stroke-width="4"/><path d="M267 158 281 166" stroke="#2d8ecb" stroke-width="4"/>
</g>'''.replace('{RECUP_PLATES}', ''.join(
  f'<path d="M{145+i*9} 128 L{153+i*9} 128 L{153+i*9} 174 L{145+i*9} 174Z" fill="{("#e59b62" if i%2==0 else "#6eacd0")}" opacity=".85" stroke="#e4ebef" stroke-width=".75"/>'
  for i in range(13)))
}
modules['ahu_section_heating_coil']={
 'name':'ПВУ · Секция водяного нагревателя','category':'ПВУ · модульные секции','description':'Водяной калорифер с ламельным пакетом, красной подачей и обратным трубным контуром.','tags':'пву секция нагревателя водяной калорифер теплообменник красный hot coil','body':'''<g>
  <path d="M116 112 261 112 277 122 132 122Z" fill="#aeb9c2" stroke="#61717e" stroke-width="1.3"/>
  <path d="M132 122 277 122 277 177 132 177Z" fill="#586a77" stroke="#c1cbd3" stroke-width="1.4"/>
  {COIL_FINS}
  <path d="M122 116 122 173" stroke="#c8783e" stroke-width="8"/>
  <path d="M122 116 C101 116 102 126 122 126 C144 126 144 138 122 138 C101 138 101 150 122 150 C144 150 144 162 122 162 C104 162 104 173 122 173" class="ahu-copper"/>
  <path d="M265 116 C286 116 286 127 265 127 C244 127 244 139 265 139 C286 139 286 151 265 151 C244 151 244 163 265 163 C281 163 281 173 265 173" class="ahu-hot"/>
  <circle cx="122" cy="116" r="5" fill="#d97d40" stroke="#723e28"/><circle cx="265" cy="173" r="5" fill="#c95239" stroke="#723e28"/>
</g>'''.replace('{COIL_FINS}', ''.join(f'<path d="M{142+i*10} 125  {142+i*10} 175" class="ahu-fin"/>' for i in range(12)))
}
modules['ahu_section_cooling_coil']={
 'name':'ПВУ · Секция водяного охладителя','category':'ПВУ · модульные секции','description':'Секция охлаждения с синим контуром холодоносителя, ламелями и поддоном конденсата.','tags':'пву секция охлаждения охладитель холодная вода синий cooling coil condensate','body':'''<g>
  <path d="M116 112 261 112 277 122 132 122Z" fill="#9fb4c4" stroke="#526a7b" stroke-width="1.3"/>
  <path d="M132 122 277 122 277 177 132 177Z" fill="#435d70" stroke="#b2c2ce" stroke-width="1.4"/>
  {COOL_FINS}
  <path d="M122 116 C101 116 102 126 122 126 C144 126 144 138 122 138 C101 138 101 150 122 150 C144 150 144 162 122 162 C104 162 104 173 122 173" class="ahu-cold"/>
  <path d="M265 116 C286 116 286 127 265 127 C244 127 244 139 265 139 C286 139 286 151 265 151 C244 151 244 163 265 163 C281 163 281 173 265 173" fill="none" stroke="#36a5e2" stroke-width="5" stroke-linecap="round"/>
  <circle cx="122" cy="116" r="5" fill="#5db5e6" stroke="#175a8a"/><circle cx="265" cy="173" r="5" fill="#2b8dcc" stroke="#175a8a"/>
  <path d="M126 182 276 182 269 190 134 190Z" fill="#9fb4c2" stroke="#516a7b" stroke-width="1.1"/>
  <path d="M134 185 267 185" stroke="#e0f3fc" stroke-width="2"/>
</g>'''.replace('{COOL_FINS}', ''.join(f'<path d="M{142+i*10} 125 {142+i*10} 175" stroke="#b5d1e1" stroke-width="1.5"/>' for i in range(12)))
}
modules['ahu_section_supply_fan']={
 'name':'ПВУ · Секция приточного вентилятора','category':'ПВУ · модульные секции','description':'Центробежный вентилятор с рабочим колесом, электродвигателем и виброопорами. Ротор вращается при Boolean/value=1.','tags':'пву вентилятор приточный радиальный центробежный fan motor rotor animated airflow','body':'''<g>
  <path d="M118 113 259 113 278 125 137 125Z" fill="#8e9da8" stroke="#d1dbe1" stroke-width="1.3"/>
  <path d="M137 125 278 125 278 180 137 180Z" fill="#283844" stroke="#82919c" stroke-width="1.5"/>
  <path d="M132 121 238 121 238 180 132 180Z" fill="#16232d" stroke="#8898a3" stroke-width="2"/>
  <path d="M157 179 258 179 270 187 169 187Z" fill="#667887" stroke="#384957" stroke-width="1.5"/>
  <g class="fan-rotor">
    <circle cx="206" cy="143" r="48" fill="#8c9ca8" stroke="#e1e7eb" stroke-width="3"/>
    <circle cx="206" cy="143" r="42" fill="#354755" stroke="#aebbc4" stroke-width="2"/>
    {FAN_BLADES}
    <circle cx="206" cy="143" r="14" fill="#2b90cf" stroke="#d4e0e7" stroke-width="3"/>
    <circle cx="206" cy="143" r="5" fill="#e8edf1" stroke="#4f6677" stroke-width="1.2"/>
  </g>
  <path d="M249 125 278 111 302 124 302 167 278 180 249 164Z" fill="#637987" stroke="#d4dee5" stroke-width="2"/>
  <rect x="276" y="118" width="37" height="34" rx="6" fill="#1678b7" stroke="#174f75" stroke-width="2"/>
  <path d="M283 123 306 123 306 147 283 147Z" fill="#329bd4" stroke="#9ecbe5" stroke-width="1.2"/>
  <path d="M288 120 288 150M294 120 294 150M300 120 300 150" stroke="#145783" stroke-width="1.4"/>
  <path d="M164 190 251 190 261 196 174 196Z" fill="#aab6bf" stroke="#5a6a76" stroke-width="1.2"/>
  <path d="M180 186 180 193M238 185 238 193" stroke="#354956" stroke-width="3"/>
</g>'''.replace('{FAN_BLADES}', ''.join(
   f'<path d="M206 140 C{206+12*__import__("math").cos(i*3.14159/4):.2f} {143+12*__import__("math").sin(i*3.14159/4):.2f} {206+37*__import__("math").cos(i*3.14159/4+.42):.2f} {143+37*__import__("math").sin(i*3.14159/4+.42):.2f} {206+31*__import__("math").cos(i*3.14159/4+.85):.2f} {143+31*__import__("math").sin(i*3.14159/4+.85):.2f} Q{206+20*__import__("math").cos(i*3.14159/4+1.0):.2f} {143+20*__import__("math").sin(i*3.14159/4+1.0):.2f} 206 140Z" fill="#c8d2d9" stroke="#536573" stroke-width="1"/>'
   for i in range(8)))
}
modules['ahu_section_open_plenum']={
 'name':'ПВУ · Открытая выходная секция после вентилятора','category':'ПВУ · модульные секции','description':'Пустая секция-удлинитель после вентилятора с открытой боковой стенкой и видимым внутренним каналом.','tags':'пву короб пустая секция plenum выходной патрубок открытая боковая стенка без панели airflow','open_outlet':True,
 'body':'''<g>
  <!-- Open box: no front/side sheet panel; only the rear liner, rails and framing remain. -->
  <path d="M103 108 292 108 333 130 333 180 103 180Z" fill="#202e39" stroke="#9aa8b2" stroke-width="2"/>
  <path d="M105 111 288 111 324 131 324 174 105 174Z" fill="#1a2a36" stroke="#5c6d79" stroke-width="1.3"/>
  <path d="M104 110 292 110 292 119 104 119Z" fill="#788793" opacity=".5"/>
  <path d="M110 176 292 176 333 198 151 198Z" fill="#9daab4" stroke="#d8e0e5" stroke-width="1.5"/>
  <path d="M104 108 104 184M292 108 292 184M333 130 333 198" stroke="#ccd5dc" stroke-width="5" fill="none"/>
  <path d="M104 108 292 108 333 130" stroke="#f0f4f6" stroke-width="4" fill="none"/>
  <path d="M104 184 292 184 333 207" stroke="#697985" stroke-width="5" fill="none"/>
  <path d="M120 127 294 127M120 162 294 162" stroke="#71818d" stroke-width="1.2" opacity=".6"/>
  <path d="M133 135 133 157M176 135 176 157M220 135 220 157M264 135 264 157" stroke="#52636f" stroke-width="1" opacity=".55"/>
</g>'''
}

for key, spec in modules.items():
    pfx=key.replace('ahu_section_','as_')+'_'
    markup=STYLE.replace('__PFX__',pfx)
    shell=chassis(pfx, open_outlet=spec.get('open_outlet',False)).replace('__PFX__',pfx)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="640" viewBox="35 62 317 185" data-avic-style="iso3d" preserveAspectRatio="xMidYMid meet" role="img" aria-labelledby="title desc">
<title id="{pfx}title">{spec['name']}</title><desc id="{pfx}desc">{spec['description']}</desc>
{markup}
{shell}
{spec['body'].replace('__PFX__',pfx)}
<g class="ahu-air-system">
  <path class="ahu-air" d="M36 133 C130 124 250 142 351 133" marker-end="url(#{pfx}arrow)"/>
  <path class="ahu-air-dash" d="M36 133 C130 124 250 142 351 133"/>
  <circle class="ahu-particle" cx="42" cy="123" r="3"/>
  <circle class="ahu-particle" cx="42" cy="145" r="2.4" style="animation-delay:.55s"/>
  <circle class="ahu-particle" cx="42" cy="134" r="2" style="animation-delay:1.1s"/>
</g>
</svg>'''
    # airflow overlay is above equipment but below the open cabinet frame label.
    # Insert flow overlay before svg close, retaining it as a separate group for animation.
    path=SVG_DIR/f'{key}.svg'
    path.write_text(svg,encoding='utf-8')
    print('created',path.name,len(svg))

# Render preview tiles in off state and on state by adding state classes to root.
preview_dir=ROOT/'docs/previews/ahu_modular'
preview_dir.mkdir(parents=True,exist_ok=True)
font_candidates=['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
font_path=next((x for x in font_candidates if Path(x).exists()),None)
font=ImageFont.truetype(font_path,16) if font_path else ImageFont.load_default()
font_small=ImageFont.truetype(font_path,12) if font_path else ImageFont.load_default()

def raster(key, states=()):
    text=(SVG_DIR/f'{key}.svg').read_text(encoding='utf-8')
    cl=' '.join(states)
    text=text.replace('<svg ',f'<svg class="{cl}" ',1)
    return cairosvg.svg2png(bytestring=text.encode('utf-8'),output_width=600,output_height=480)

# Individual render states (note CairoSVG renders geometry and static states; browser animates CSS keyframes).
for key,spec in modules.items():
    states=['state-airflow']
    if key=='ahu_section_outdoor_damper': states += ['state-damper-open']
    if key=='ahu_section_supply_fan': states += ['state-fan-running']
    (preview_dir/f'{key}_preview.png').write_bytes(raster(key,states))

# contact sheet, two rows with 4 columns (last slot blank).
thumbs=[]
for key,spec in modules.items():
    im=Image.open(preview_dir/f'{key}_preview.png').convert('RGBA')
    im.thumbnail((410,328),Image.Resampling.LANCZOS)
    card=Image.new('RGBA',(440,390),'white')
    card.alpha_composite(im,((440-im.width)//2,5))
    d=ImageDraw.Draw(card)
    label=spec['name'].replace('ПВУ · ','')
    d.text((18,348),label,font=font,fill='#1e2933')
    d.text((18,370),'Одинаковый корпус / общий габарит / общий стык',font=font_small,fill='#637381')
    thumbs.append(card)
sheet=Image.new('RGBA',(440*4,390*2),(244,246,248,255))
for i,im in enumerate(thumbs):sheet.alpha_composite(im,((i%4)*440,(i//4)*390))
sheet.save(preview_dir/'AVIC_AHU_Modular_Sections_Contact_Sheet.png')

# Composite assembly preview is scaled to the exact Graphics element width (286 units).
combined=[]
module_width=286
scale=module_width/317
assembly_width=module_width*len(modules)
assembly_height=185*scale
for i,key in enumerate(modules):
    inner=(SVG_DIR/f"{key}.svg").read_text(encoding='utf-8').split("<svg",1)[1].split(">",1)[1].rsplit("</svg>",1)[0]
    # Convert the shared source viewBox origin to local zero, then scale each module identically.
    combined.append(f'<g transform="translate({i*module_width},0) scale({scale:.8f}) translate(-35,-62)">{inner}</g>')
assembly=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{assembly_width}" height="{assembly_height:.3f}" viewBox="0 0 {assembly_width} {assembly_height:.3f}"><rect x="0" y="0" width="{assembly_width}" height="{assembly_height:.3f}" fill="#ffffff"/>{''.join(combined)}</svg>'''
(preview_dir/'AVIC_AHU_7_Section_Assembly.svg').write_text(assembly,encoding='utf-8')
cairosvg.svg2png(bytestring=assembly.encode(),write_to=str(preview_dir/'AVIC_AHU_7_Section_Assembly.png'),output_width=2600,output_height=217)

# manifest
manifest={key:{'name':v['name'],'category':v['category'],'description':v['description'],'tags':v['tags'],'svg_url':f'/api/graphics/library/{key}/svg','animation':({'damper':key=='ahu_section_outdoor_damper','fan':key=='ahu_section_supply_fan','airflow':'global fan AND inlet damper active'})} for key,v in modules.items()}
(preview_dir/'MANIFEST_RU.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('preview',preview_dir)
