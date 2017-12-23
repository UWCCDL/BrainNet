import CCDLUtil.DataManagement.FileParser as CCDLFP
import Constants
import random

def main():

    for condition in range(6):
        random.seed(condition * 17)
        exp_trials = [Constants.EXPERIMENTAL_STR] * Constants.NUM_EXP_TRIALS
        control_trials = [Constants.CONTROL_STR] * Constants.NUM_CONTROL_TRIALS
        trials = exp_trials + control_trials
        random.shuffle(trials)
        print 'ref/Condition%d.yaml' % condition
        CCDLFP.save_yaml_file('ref/Condition%d.yaml' % condition, data=trials)

if __name__ == '__main__':
    main()