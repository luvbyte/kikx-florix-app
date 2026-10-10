from .ui import Pre, Div, Animate
from flx.ui.elements import IFrame



B1 = Animate(Pre(Div(r"""
♡  /)/)
 （„• ֊ •„)♡              
┏ • UU • - • - • - • - • - • - • ღ❦ღ┓
              <span class="text-blue-300 font-bold">FLORIX NEKO</span> 
            A <span class="text-red-300">Script</span> Runner 
┗ღ❦ღ • - • - • - • - • - • - • - •  ┛
     \(•.•)/              \(•.•)/
       | |                  | |
      _/ \_                _/ \_
/````````````````````````````````````\
""")))
B1.add_class("w-full h-full flex items-end justify-center")

B2 = Animate(Pre(Div(r"""
  /)/) E            K (\(\
 (•.•)/              \(•.•)
N/| |      FLORIX      | |\O
 _/ \_                _/ \_
""")), "slideInUp")
B2.add_class("w-full h-full flex items-end justify-center text-sm")

B3 = Animate(Pre(Div(r"""
(`“ •.  (`“•.¸🌼¸.•“´)  ¸. •“´)
    🌸«•🍃   NEKO  🍃•“»🌸
(¸. • “´(¸.•“´🌼 `“•)` “° •.¸)
""")), "rubberBand")
B3.add_class("w-full h-full flex items-center justify-center")

B4 = Animate(Pre(Div(r"""
   /)/)  FLORIX
  (•.•)丿  X   NEKO
ノ/   /  
ノ￣ゝ 
""")), "lightSpeedInLeft")
B4.add_class("w-full h-full flex justify-start items-end text-sm")


BANNERS = [B1, B3, B2, B4]

