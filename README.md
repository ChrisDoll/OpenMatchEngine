<!-- -------------------------------------------------------------------
 📣  FM24   |   MATCH-ENGINE TOOLKIT
--------------------------------------------------------------------- -->

# 🏟️  An Open Easy to use solution for **FM24 Match Engine editing**

The last half year has seen a small explosion in the number of custom match engines being made for Football Manager.  
This is an attempt to make the creation of such custom changes more accessible and less of a black box, not only concerning the "match engine" itself, but also the player selection AI and player rating system (the 6.7 score awarded to each player in the game).

> **TL;DR**&nbsp;— Three editable files power the engine, squad-selection AI, and in-match ratings.  
> Instead of attempting to deliever the *best* changes to these files, this project focuses on speeding up the iteration process of match engine tweaks, hopefully paving the way for better future match engines.

---

## 📑 Table of Contents
| Section | Jump |
|---------|------|
| 1&nbsp;&nbsp;—&nbsp;[Project Files](#project-files) |
| 2&nbsp;&nbsp;—&nbsp;[Usage Instructions](#usage-instructions) |
| 3&nbsp;&nbsp;—&nbsp;[Additional Notes](#additional-notes) |
| 4&nbsp;&nbsp;—&nbsp;[How Does Decoding Work?](#how-does-decoding-jsb-files-work) |

---

## 1 — Project Files  <a id="project-files"></a>

| File | Purpose (from the author, verbatim) |
|------|-------------------------------------|
| **(1) `physcial_constraints.json`** | *“Controls a set of functional parammeters that determines the movement speed, kicking speed and reaction time of players on the field in FM. … This is what has been traditionally discussed as the Match engine file.”* |
| **(2) `weights.json`** | *“Determines how the AI will select the squad for each match.”* |
| **(3) `Player_ratings_data.xslx`** | *“Controls the player rating system … converted it to an excel document which greatly simplifies the process.”* |

---

### 1.1  `physcial_constraints.json`

This is the file that controls a set of functional parammeters that determines the movement speed, kicking speed and reaction time of players on the field in FM. This is what has been traditionally discussed as the Match engine file.  
In many ways, this is a limited way to change the match engine. There is no such thing as simply "increasing the viability of counter-attacks", "improving ball physics" or "increasing the challenge of the game" by changing these values.  
Instead, you need to think hard about how changing these values will have downstream effects on the way the game is played inside FM.

<details>
<summary>💡 Example (verbatim)</summary>

I want to increase the level of positioning of players on the field.  
This is clearly a movement related change, though for many changes they might easily fall between categories.  
Lets say, I increase the speed of slow movement in the game: **`very_slow_walk_speed`**, **`slow_walk_speed`** and **`walk_speed`** ⬆️

Why could this result in better positioning? Because the primary time players move around slowly, is when repositioning before active play.  
As such, when we increase players movement at low speed, it **(probably\*)** has an indirect effect of making them get to their position faster.  
Why probably? Because ultimately this is just theoretical and I won't know until i actually try it out *a lot* ingame, due to the level of "randomness" in the engine making placeebo effects incredibly common.  
Additionally, it might also have unexpected consequences. The above change probably makes defense stronger, due to defenders spending more time at low speed than midfielders. It might make poachers stronger by making their roaming more effective.

As such, we should think hard about what changes we make, what effects we expect them to have and whether we actually observe that in game, or if we are just observing placebo.

That is not to throw shade at exsisting match engines, this is a very new type of mod for FM. But when claims are made like a match engine mod revolutionizing play on the field, enabeling new tactics or fundamentally increasing both the realism and challenge of FM, people should be generally skeptical.  
It is almost certainly never true that any change to the match engine results in objective improvement to play. Neither is it possible to make credible claims about what *exactly* any given changes to the match engine accomplishes.  
For that reason, the standard approach should also be for people who make match engines, to:  

1. be clear about what values they actually change,  
2. what effect they hope it will have on the game and  
3. the extend to which they have actually tested it.
</details>

---

### 1.2  `weights.json`

This file is the parameters which determines how the AI will select the squad for each match.  
Internally it contains two groups of values, the first set of values which **(probably\*)** control the selection whenever the user is invovled, that is, the recommendation your Assistant Coach gives you before each game.  
The second set of values **(probably\*)** controls the AI's selection for all other games, which requires it to ignore certain limitations the user faces, but which the AI does not, ie. the ai doesn't care about rest promises for example.

These values effectively just weight which criteria the AI should use when selecting players. How much value should be put on general ability vs role ability. Reputation vs condition. Etc.

---

### 1.3  `Player_ratings_data.xslx`

Editing the player ratings file is very new. In fact the only ones who I know to have done it is the FM Match Lab team. That is for a very simple reason, the file which controls the player rating system is a bit of a mess.  
So I converted it to an excel document which greatly simplifies the process of making changes to the player ratings values, grouping the relevant roles together along with the values assigned to them at the outset.

> *Want to give Central defenders a small boost to their ratings?* Bump their reward for successful tackles or intercepts by 10/20.  
> *Feel like your wide target forward is always getting shafted?* Increase their reward for assists by 50.  
> Or just recognize that one is a bad role which can't be fixed.

\* This is a qualified guess, it may eventually turn out wrong

---

## 2 — 🛠️ Usage Instructions

> The **only** requirement for running this repo is having **Python installed**.  
> If you’ve never installed Python before, don’t worry—it’s quick, easy, and far safer than downloading a random executable from a sketchy forum.

---

### 📂 Preparation

1. **Download** the repo and extract it to a folder of your choice.  
   > *More pre-tuned versions with ready-made changes are coming soon.*

2. **Edit** the three editable files:  
   * `physical_constraints.json` & `weights.json` — use any text editor (e.g., Notepad).  
   * `Player_ratings_data.xlsx` — open in Excel or Google Sheets.

3. **Run** the build script:
   **python prepare_simatch.py**

*If double-clicking doesn’t work, look up how to execute a Python script from the command line.*  
This creates a new folder called **`simatch`** alongside the repo.

---

### 🛠️ Build the FMF

1. **Install** the **Football Manager Resource Archive** tool (Steam → **Tools** tab).  
   *Make sure “Tools” are enabled in your Steam library view.*

2. **Create** the file FM24 will read:

   1. Open **Football Manager Resource Archive** → click **Create**.  
   2. **Source folder** → select the newly-created **`simatch`** folder.  
   3. **Destination for `simatch.fmf`** → choose one of the following:

      | Option | Path / Action | Notes |
      |--------|---------------|-------|
      | **A — Direct overwrite** | `C:\Program Files (x86)\Steam\steamapps\common\Football Manager 2024\data` | Overwrites the existing `simatch.fmf`. A backup of the original is included in `src/`. |
      | **B — Manual move** | Any folder you like | After creation, move the new `simatch.fmf` to your `Football Manager 2024\data` (or equivalent) directory. |

---

### 🎮 Final Check

1. **Launch FM24** and load a save.  
2. If the save loads successfully, everything is working as intended—enjoy! 🎉


## 3 — Additional Notes <a id="additional-notes"></a>

The repo also includes the tools I used to **decode the original `simatch.fmf` from SI**.  
There are **three Python scripts**—one for each editable file—written in the same style as `prepare_simatch.py`.

> These scripts let you reverse-engineer *any* edited match engine you download from your favourite modder.

**Workflow**

1. Use **Football Manager Resource Archive** to extract the downloaded `simatch.fmf` into a folder.  
2. To decode the extracted `physical_constraints.jsb` (or the other `.jsb` files), choose **one** of the following:

   * **Option A — Edit the script**  
     *Open* `decode_physical_constraints.py` and change the target path to point at the `.jsb` file you just extracted.

   * **Option B — Replace the clean folder**  
     Replace the contents of the `clean_simatch` folder with the files from the modded match engine, then run the script as-is.

---

## 4 — How does decoding `.jsb` files work? <a id="how-does-decoding-jsb-files-work"></a>

Fundamentally, SI’s `.jsb` files are just **“lightly” encoded JSON**.

* Using a hex-editor like **ImHex** you’ll notice mostly plain UTF-8 key strings paired with little-endian byte values.  
* The exact encoding scheme isn’t public, so simply “reversing” it isn’t possible.

Each decode script is therefore slight controlled chaos:

1. Jump to a **hard-coded start address** found by trial and error.  
2. **Read key–value pairs** sequentially.  
3. **Reconstruct** the original JSON structure—partly by semi-automated parsing, partly by educated guessing based on the hex dump.

