# THE WARDEN -- boss of act 1. A jailer the size of a gatehouse: slow, swung, crushing.
# 12/8 (four dotted beats a bar) in D phrygian, chains on every beat. Layer 0 is the fight; layer 1 is its rage (below half health).

piece zeal_warden_l1 key="D minor" tempo=156 meter=12/8 style=electronic
master room.decay=2.2 room.wet=0.24 push=3

section a  bars=4 dynamic=ff
section b  bars=4 dynamic=ff
section a2 bars=4 dynamic=ff
section c  bars=4 dynamic=ff

harmony
  @a:  i5 i5 i5 bII5
  @b:  VI5 VI5 iv5 bII5
  @a2: i5 i5 i5 bII5
  @c:  i5 i5 bII5 V

motif wa1 = 0! r 0 0! r 0 b1! r b1 0! r r            -- the swing: long-short, long-short, a lean on the flat second
motif wa2 = 0! r 0 0! r 0 b4! 4 b4 2! b1 0           -- answered through the tritone
motif wa3 = 0! r 0 0! r 0 7! 6 5 b4! 2 b1            -- and a fall from the octave
motif wb1 = 5! r 5 5! r 5 4! r 4 b4! r r             -- the same swing a sixth up, sinking by half steps
motif wb2 = 2! r 2 2! r 2 b1! b1 b1 b1! b1 b1
motif wb3 = 5! r 5 4! r 4 b4! r b4 2! b1 0
motif wc1 = 0:3/8! r:3/8 0:3/8! b1:3/8!              -- the stomp: three blows and a lean
motif wc2 = b1:3/8! r:3/8 b1:3/8! b4:3/8!
motif wc3 = 0! 0 0 b1! b1 b1 b4! b4 b4 4! b4 7       -- twelve eighths straight up the wall
motif zeal = 0:3/4 b1:3/8 2:3/8 | 4:3/4 b4:3/4 | 4:3/8 b4:3/8 4:3/8 7:3/8 | 7:3/2      -- the game's theme, stretched over the swing
motif zeal_inv < zeal : invert
motif chain = 4:3/4! 4:3/4                            -- iron on beats one and three
motif knell = 0:3/2                                  -- one bell a bar

lanes DOOM
  kick:  x.x.....x...|x.x..x..x.x.
  snare: ......X.....
  bell:  x..x..x..x..
lanes DOOMFILL
  kick:  x.x.....x...
  snare: ......X..xxx
  tom_lo: .........x.x
  tom_mid: ..........x.
lanes STOMP
  kick:  x..x..x..x..
  snare: ...X.....X..
  crash: x.....x.....
lanes RAGE
  snare: .....x.....x|..x..x..x.xx
  hat:   x.xx.xx.xx.x
  open:  ..x.....x...
set ONE = "x..........."

voice lead monster_lead role=melody octave=4 engine=soundfont
  l_a: play motif=zeal at=@a dynamic=ff
  l_b: play motif=zeal_inv at=@b transpose=5 dynamic=ff
  l_a2: play motif=zeal at=@a2 octave=5 dynamic=ff
  l_c: play motif=wc1 at=@c times=2 octave=5 dynamic=ff
  l_c3: play motif=wc2 at=@c.3 octave=5 dynamic=ff
  l_c4: play motif=wc3 at=@c.4 octave=5 dynamic=ff
  fx_lead: drive amount=0.4
  fx_lead_dark: filter start=4200 end=4200
  fx_lead_hp: filter mode=highpass start=180 end=180
  fx_lead_cut: eq freq=1800 gain=2 width=1.2
  lvl_lead: gain db=0
voice machine kit_tr909 role=percussion engine=soundfont
  for sec in a b a2 c
    m_{sec}: beat at=@{sec} bars=4 lanes=$RAGE res=1/8 tune=5 dynamic=ff
    m_roll_{sec}: chop in=@{sec}.4-4 slices=12 order="0 1 2 3*2 4 5*2 6*2 7*2 8*4 9*4 10*4 11*4^0>12"
  fx_m_thin: filter mode=highpass start=300 end=300
  fx_m_teeth: eq freq=1300 gain=5 width=1.4
  fx_m_crush: crush rate=16000 bits=8
  fx_m_drive: drive amount=0.8 mode=clip
  fx_m_slab: compress ratio=8 threshold=-24
  lvl_m: gain db=4
voice siren screamer role=counter octave=5 pan=-0.3 engine=soundfont
  for sec in b c
    sir_{sec}: phrase at=@{sec}.4 steps="7:3/8 r:3/8 b8:3/8 r:3/8" dynamic=f
  fx_siren_lo: filter mode=highpass start=700 end=700
  fx_siren_hi: filter start=3400 end=3400
  fx_siren_edge: eq freq=3200 gain=-3 width=1.0
  lvl_siren: gain db=8
