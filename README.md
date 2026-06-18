# **Myo Programming Language Manual**

Welcome to the official developer guide for **Myo**, a high-performance, object-oriented programming language designed specifically for real-time 2D and 3D games.

Myo combines a clean, Pythonic syntax (using def, class, and import) with explicitly bounded structural closures ({} block styling), manual execution paradigms, and direct OS/GPU integrations.

## **1\. Syntax & Structural Overview**

Myo files use the .myo extension. The syntax is designed to be highly readable, prioritizing simplicity while retaining explicit block boundaries.

### **Core Keywords**

* **class**: Defines an object-oriented capsule.  
* **def**: Declares a block-level function or method.  
* **create**: The class constructor method (automatically executed upon instantiation).  
* **object**: The self-referencing pointer representing the active class instance (replaces this or self).  
* **import**: Exposes system modules (e.g., graphics, input, math).  
* **if**: Conditionally branches game logic.

### **Lexical Elements**

* **Comments**: Prefixed with \# and discarded at compile-time.  
* **Variables**: Dynamically allocated but implicitly treated as single-precision floating-point numbers (float\_t) in the runtime for maximum performance.  
* **Braces**: { and } explicitly define statement blocks. Unlike Python, whitespace indentation is ignored, although clean indentation is highly recommended.

## **2\. Basic Language Concepts**

### **Variables and Assignment**

Variable declaration is implicit. Assigning a value to a name automatically binds it to the local scope:

speed \= 450.0  
name \= "MyoEngine"

### **Mathematical Operators**

Myo supports standard arithmetic expressions:

* **\+** (Addition)  
* **\-** (Subtraction)  
* **\*** (Multiplication)  
* **/** (Division)

dx \= speed \* dt  
total \= (a \+ b) / 2.0

### **Conditional Logic & Comparisons**

The if statement evaluates numeric values. Any non-zero value evaluates as true, while exactly 0.0 is treated as false.

Supported comparison operators are:

* **\<** (Less than)  
* **\>** (Greater than)  
* **\<=** (Less than or equal)  
* **\>=** (Greater than or equal)  
* **\==** (Equal to)  
* **\!=** (Not equal to)

if object.px \< 15.0 {  
    object.px \= 15.0  
}

## **3\. Object-Oriented Blueprint**

Myo uses a structural class model. Every variable assigned to object is preserved as a permanent instance attribute (or static LLVM global variable in Ahead-Of-Time compiled binaries).

### **Defining a Class**

class Vector {  
    def create(x, y) {  
        object.x \= x  
        object.y \= y  
    }

    def reset() {  
        object.x \= 0.0  
        object.y \= 0.0  
    }  
}

### **Instantiation**

To create an instance of a class, call the class name as a function:

position \= Vector(100.0, 250.0)

## **4\. Built-in Standard Modules**

Myo includes pre-bound libraries for handling hardware windows, inputs, and math calculations natively.

### **🎨 The graphics Module**

This module handles double-buffered, low-latency viewport presentation.

* **graphics.init(width, height, title)** *(Interpreter mode only)*  
  Opens a desktop window viewport of specified dimensions.  
* **graphics.clear(r, g, b)**  
  Clears the active backbuffer frame to the specified RGB values (0.0 to 255.0).  
* **graphics.draw\_rect(x, y, w, h, r, g, b)**  
  Draws a solid rectangle on the screen.  
* **graphics.draw\_circle(cx, cy, radius, r, g, b)**  
  Draws a solid circular/elliptical block centered at (cx, cy).  
* **graphics.draw\_score(score, x, y)**  
  Renders a high-resolution text representation of the score value at coordinates (x, y).

### **⌨️ The input Module**

Interrogates current hardware keyboard states.

* **input.is\_key\_down(vk\_code)**  
  Returns 1.0 if the specified hardware virtual key is currently pressed; otherwise returns 0.0.  
  **Common Win32 Virtual Key Codes (floats):**  
  * 37.0: Left Arrow  
  * 38.0: Up Arrow  
  * 39.0: Right Arrow  
  * 40.0: Down Arrow  
  * 32.0: Spacebar  
  * 87.0: W Key  
  * 83.0: S Key

### **🧮 The math Module**

* **math.rand(low, high)**  
  Generates a random float value between low and high.

## **5\. Lifecycle Hooks**

A standard Myo program coordinates through global engine lifecycle entries. The compiler maps these to native machine loops:

1. **config()** *(Optional)*: Configures the initial window title, width, and height.  
2. **class Player**: The core application state driver.  
   * **def create()**: Executes **once** on engine startup to initialize variables.  
   * **def update()**: Executes **60 times per second** to process inputs, physics, collisions, and draw graphics.

## **6\. Complete Sample Game Code**

Below is a complete, fully playable **Star Catcher** game showcasing Myo's language mechanics:

\# star\_catcher.myo  
import graphics  
import input  
import math

class Player {  
    def create() {  
        \# Initialize Player position at the bottom of the screen  
        object.px \= 590.0  
        object.py \= 560.0  
          
        \# Initialize Golden Star falling state  
        object.star\_x \= 300.0  
        object.star\_y \= 50.0  
        object.star\_speed \= 6.0  
          
        \# Initialize Score accumulator  
        object.score \= 0.0  
    }

    def update() {  
        \# 1\. Capture Keyboard Inputs & Move Paddle  
        if input.is\_key\_down(37.0) { \# 37.0 is the Left Arrow key  
            object.px \= object.px \- 12.0  
            if object.px \< 15.0 {  
                object.px \= 15.0  
            }  
        }  
        if input.is\_key\_down(39.0) { \# 39.0 is the Right Arrow key  
            object.px \= object.px \+ 12.0  
            if object.px \> 1150.0 {  
                object.px \= 1150.0  
            }  
        }

        \# 2\. Physics: Move the star downwards  
        object.star\_y \= object.star\_y \+ object.star\_speed  
          
        \# Reset the star if it falls past the screen  
        if object.star\_y \> 640.0 {  
            object.star\_y \= 30.0  
            object.star\_x \= math.rand(100.0, 1080.0)  
            object.star\_speed \= 6.0  
        }

        \# 3\. Collision Detection: Paddle catching the falling star  
        if object.star\_y \> 540.0 {  
            if object.star\_y \< 570.0 {  
                if object.star\_x \> object.px \- 15.0 {  
                    if object.star\_x \< object.px \+ 120.0 {  
                        object.score \= object.score \+ 1.0  
                        object.star\_y \= 30.0  
                        object.star\_x \= math.rand(100.0, 1080.0)  
                        \# Scale up speed to slowly increase difficulty  
                        object.star\_speed \= object.star\_speed \+ 0.8  
                    }  
                }  
            }  
        }

        \# 4\. Rendering Pipeline  
        \# Clear backbuffer with deep space color  
        graphics.clear(18.0, 18.0, 32.0)

        \# Draw Player Paddle (Neon Green)  
        graphics.draw\_rect(object.px, 560.0, 115.0, 20.0, 46.0, 204.0, 113.0)

        \# Draw Falling Star (Gold Circular block)  
        graphics.draw\_circle(object.star\_x, object.star\_y, 12.0, 241.0, 196.0, 15.0)

        \# Output HUD Score Text  
        graphics.draw\_score(object.score, 40.0, 30.0)  
    }  
}

## **7\. Running & Building Games**

Using your bundled myo executable, you can choose between rapid prototyping or optimized native builds.

### **Direct Play Mode (Interpreted)**

Runs the game instantly through Pygame for development:

myo run star\_catcher.myo

### **Production Build Mode (AOT Native Compilation)**

Compiles down to optimized LLVM Intermediate Representation (.ll), links against the standalone high-performance hardware engine, and outputs a standalone machine binary:

myo build star\_catcher.myo \--to star\_catcher.exe

