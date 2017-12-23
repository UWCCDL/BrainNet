# Brain-to-Brain Network

### Author - Darby Losey (loseydm@uw.edu) Spring 2017

# Naming Conventions

C0 refers to the TMS (alpha) computer
C1 refers to the SSVEP computer
C2 refers to the Motor Imagery computer

CX subject, refers to the participant seated at computer X.
CX experimenter refers to the experimenter monitoring the subject seated at computer X.

Target Piece - the piece that subjects are trying to turn or not turn.
Bottom - All the pieces at the bottom of the board.  
These are all other pieces on the board that are not the target piece.

# Algorithm

##### Unless otherwise noted, this is from the perspective of C0

Prior to experiment:
    * Training for Subject C2 (Motor Imagery)
        [Still TBD on how this will be done]
    * Thresholding for TMS subject
    * Reading subject instructions, showing examples
    
0. SETUP - Receive Input from Users (stating condition, subject number, etc.).
    1. Start board with randomized 'starting' layer.
    2. Wait for other computers to start game (Showing crosshairs on all 3 screens)
    3. Generate starting board
1. Wait for C0 Experimenter to hit the "Start Button"
    1. C0 Experimenter places the control prop in place if specified.
    2. Control conditions are 1/3 of the trials (selected randomly)
2. Send out board to C1 and C2 (this marks the 'go' button)
3. Wait for both C1 and C2 to respond with the user's answer.
4. C1/C2 Subroutine


    The C1/C2 Subroutine :
    2a. C1/C2 update their model of the board
    2b. C1/C2 Show the board (hiding the crosshairs). Top piece is visible.
    2c. For C1, lights turn on
    2c. Wait 2 seconds
    2d. Cursor shows up at the top of the screen (above the block game)
        2d-2. Cursor moves horizontally, providing feedback.
    2e. Begin the respective BCI, providing feedback via the cursor.
    2f. Stop collecting data
    2g. Show Crosshairs, Turn off lights
    2e. Send result to C0.
    
    Note 1: After each step, send C0 an updated message reporting the progress. This will
     be shown to the c0 experimenter (but not the subject).  This allows the experimenter
      to track the progress of the experiment. 
     
    Note 2: The experiment will be double-blind to the C0 experimenter as they will
            not see if the piece needs to be rotated or not until it is revealed to the 
            C0 subject.  For obvious reasons, this will not be the case for the C1 and C2
            Experimenters.
      
5. C0 TMS subroutine


    The C0 TMS subroutine: 
    1. Set TMS intensity
    2. Flash crosshair red (for TMS warning)
    3. Fire at TMS intensity as determined by CX (either C0 or C1 as determined by the counterbalanced experiment 
         condition).  This will require number of experiments to be a multiple of 2.
         
         3b. High Intensity (Phosphene) will always mean 'ROTATE'. Low Intensity (No Phosphene) will always mean "DON'T ROTATE"
         3c. The label 0 is always rotate mean rotate.

    4. Wait 8 seconds, Flash crosshairs red, Fire TMS intensity according to other CX (opposite CX of last TMS pulse)
    5. Wait 2 second
    6. Run Alpha BCI - NO CURSOR TASK FEEDBACK PROVIDED
        6a. Show screen with the following messsage
            "Close your eyes to ROTATE the piece (Phosphene)
             Keep your eyes open to NOT ROTATE the Piece (No Phosphene)"
             The board with the bottom greyed out and target piece hidden will be shown below this message.
        6b. Wait 2 seconds.
        6c. Collect data - Not providing live cursor-task feedback to the subject.
            6c-1.  [Still TBD on time required for classification]
        6d. Low tone - 0.5 second beep will provide the start cue.
        6e. Show either the text "You ROTATED the piece" or "You did NOT ROTATE the piece"

6. Update the board
    1. Changed -> <s>Drop the target piece 20% down the board (i.e. the falling Tetris piece)</s>
        1. Instead the piece will remain at the same height. A "First Round" or a "Second Round" message will appear onscreen
        2. This is so that all trials are comparable when running accuracy statistics.
    2. Rotate the target piece if needed.
7. Send the new board to C1 and C2, which triggers the C1/C2 subroutine.
8. (Simultaneous with step 6) Wait 2 seconds for the C0 subject to read the "You Did/Didn't rotate the piece text". Return their screen to the crosshair
9. Wait for both C1 and C2 to respond with the turn or not turn command.
10. C0 TMS subroutine
11. Update the board.
    1. Rotate the piece if needed
    2. Drop the piece to the bottom of the board.
    3. Do Not remove completed lines.
12. Show Completed board to C0, C1, and C2.
    1. Completed board shown with message "Success" or "Failure"
    2. Completed board has the target piece on the bottom in color,
    while the rest of the bottom is in greyscale.
13. Remove completed rows
14. C0 saves completed board to disk, so it can be reloaded if there is a problem. Log all information from this trial.
15. Select a new piece according to the following algorithm:
    1. Find the minimum unfilled y location on the board (closest to the bottom) that would be 
     reachable by a dropped target piece. If there is a tie between two locations, select between the 
    ties at random.
    2. Provide a 3 by 2 target piece that is a complement to the selected bottom layer.
       Add a random third layer to this piece (making it 3x3) such that no gaps are introduced
       into this piece.
    3. Assert that this piece is not symmetric (not changed if rotated 180 degrees). If it is, generate
        a different new piece.
16. Repeat (starting from step 1)
    1. [TBD how many trials are needed; 30% (?) are control trials]

# Structure

### Dependencies
Requires that CCDLUtil be in the working path. Other dependencies include pyaml, json, numpy, pygame, wxpython.
Runs python 2.7.

### Graphics

#### How the Block Game works

The block game is separated (though this separation is not visible to the user) into 
discrete channels that are 3 columns wide.  This is done to ensure that it is always
simple to see how the piece should fit into the bottom rows of the board. No guide lines
are provided to help align the pieces.

All 3 computers make use of the BlockGame module,
which inherits from CCDLUtil/Graphics/CursorTask.

### Queue and Networking Structure

C0 will have 2 screens.  One of the screens is shown to the subject and will show all the necessary elements
(such as the cursor task and game board). The second screen (Called the QM screen) will be shown only to the C0 experimenter.

##### QM Screen queues
The QM screen reads from 3 queues:
1. c0_qm_queue
2. c1_qm_queue
3. c2_qm_queue

Each element placed on the c1 and c2 queues is a string that shows the current
state of the c1/c2 bci. Items placed on the C0 queue show aggregate info on the experiment
(such as trial index)


##### Send/Receive Queues:

These queues are for communications between C0 and C1 or C0 and C2. There
is no communication channel between C1 and C2. 

Only messages (as indicated in the Messages.py) are valid to be placed in these queues. Anything
else will raise a ValueError.

### Log Files

C0/C1/C2:
C0, C1 and C2, will continuously save all EEG data, from the start of the experiment
until its termination.  This is saved locally with the naming conventions of the EEG system used.

* C0 Log File -- Contains all information relevant to C0, logged via the C0_LOG_QUEUE
* C1 Log File -- Contains all event information related to computer C1 via the C1_LOG_QUEUE.
* C2 Log File -- Contains all event information related to computer C1 via the C2_LOG_QUEUE.

The C1 and C2 Log files contain information, such as the start/stop times of the C1/C2 BCI, event markers and other C1/C2 related activities.
The information contained in C1 and C2 log files should generally not be needed for statistics about the experiment (such as accuracies),
but are kept for completeness sake.
