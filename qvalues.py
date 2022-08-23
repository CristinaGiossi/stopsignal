from frontendhelpers import *
from tracetype import *
import copy
import pdb
import numpy as np
import scipy.stats as sp_st


# ----------------------  get_reward_value() FUNCTION  -------------------
# get_reward_value accesses the reward value for a chosen action and trial
# number. The reward value was generated by the reward generator module

# inputs:   t1_epochs = rewards generated for action 1 and n trials, shape: 1xn
#           t2_epochs = rewards generated for action 2 and n trials, shape: 1xn
#           chosen_action = action selected for this trial
#           trial_num = current trial number
# outputs:  reward_val = reward value for action chosen in the current trial
# Notes :----------------------------------------------- (temporary, remov
# At some point we have to replace one variable/action(eg t1_epochs, t2_epochs ) by a single data structure.
# Change this function accordingly. We also have to decide if the format is n_trials x channels or the otherway round
# And maybe this function does not belong in init_params.py. It felt too
# specific for frontendhelpers.py too. Find a place


# def get_reward_value(t1_epochs, t2_epochs, chosen_action, trial_num):
def get_reward_value(t_epochs, chosen_action, trial_num):

    #rew_epochs = np.vstack((t1_epochs, t2_epochs)).T

    # Assuming a n_trials x channels array

    # chosen_action - 1  because, action labels start from 1, but the index in
    # the reward array should start from 0
    #reward_val = rew_epochs[trial_num][chosen_action - 1]
    reward_val = t_epochs.iloc[trial_num][chosen_action]
    # print(reward_val)
    return reward_val


# ----------------------helper_init_Q_support_params() FUNCTION  ---------
# helper_init_Q_support_params set the parameters for Q-learning algorithm with either the defaults or the values passed as arguments.
# inputs:   q_support = Q-learning related parameters sent as argument. This is a dictionary and allows setting only a subset of the parameters
#			bayes_unif_min, bayes_unif_max: min and max for the uniform distribution with reward_value as mean
#           bayes_H:
#           bayes_sF: variance for normal pdf
#           q_alpha: Q-value learning rate
#           dpmn_CPP_scale: CPP related scale to modulate dopamine level
#           reward_value: action related reward values, initialized but overwritten by rewards generated by reward generator module
#           chosen_action: chosen action this trial (overwritten every trial)
# outputs:  Q_support_params = Q-learning related parameters

def helper_init_Q_support_params(q_support=None):

    Q_support_params = ParamSet('Q_support_params',
                                {'bayes_unif_min': 0.,
                                 'bayes_unif_max': 2.0,
                                 'bayes_H': 0.05,
                                 'bayes_sF': 1.25,
                                 'q_alpha': 0.45,  # 0.05 in original value, in working version 0.45
                                 'dpmn_CPP_scale': 35.,
                                 # 'dpmn_CPP_scale': 15.,
                                 # 'dpmn_CPP_scale': 25.,
                                 'reward_value': -1.,
                                 'chosen_action': 1})

    print("q_support", q_support)

    if q_support is not None:

        Q_support_params = ModifyViaSelector(Q_support_params, q_support)

    # print(Q_support_params['dpmn_CPP_scale'])
    return Q_support_params

# ----------------------helper_update_Q_support_params() FUNCTION  -------
# helper_update_Q_support_params updates parameters for Q-learning algorithm on every trial
# inputs:   Q_support_params = Q-learning related parameters, maintains some constant values (set at the beginning of the simulation, and variables, which are updated every trial)
#			reward_val = updates Q_support_params.reward_value with the new reward value depending on current trial number and chosen action
#           chosen_action = updates Q_support_params.chosen_action with chosen action number in the current trial
# outputs:  Q_support_params = updated Q-learning related parameters


def helper_update_Q_support_params(
        Q_support_params,
        reward_val,
        chosen_action):

    Q_support_params = untrace(Q_support_params)

    Q_support_params.reward_value = reward_val
    Q_support_params.chosen_action = chosen_action

    return Q_support_params

# ----------------------helper_init_Q_df() FUNCTION  ---------------------
# helper_init_Q_df initializes the Q-value data frame (n trials x k action channels). A new row is added to the dataframe every trial
# inputs:   actionchannels = dataframe related to the action channels. The
# action channels become the columns in a Q-value data frame.

# outputs:  Q_df = Q-value data frame


def helper_init_Q_df(actionchannels, q_df=None):

    # print(actionchannels)
    num_actions = len(actionchannels["action"])
    # print("num_actions", num_actions)
    Q_df = pd.DataFrame(
        columns=[
            untrace(
                actionchannels.iloc[na]["action"]) for na in np.arange(num_actions)])
    Q_df = Q_df.append(
        {column: 0.5 for column in Q_df.columns}, ignore_index=True)
    # Different initial values for Q_df should be taken care when calling this function with q_df and non-None value
    # eg. q_df = pd.DataFrame({1: 0.5, 2: 0.6})

    if q_df is not None:
        Q_df = pd.DataFrame(
            columns=[
                untrace(
                    actionchannels.iloc[na]["action"]) for na in np.arange(num_actions)])
        print("Q_df", Q_df)
        Q_df = Q_df.append(
            {column: 0.5 for column in Q_df.columns}, ignore_index=True)

        Q_df = ModifyViaSelector(Q_df, q_df)

    return Q_df

# ---------------------- helper_update_Q_df() FUNCTION  -------------------
# helper_update_Q_df updates the Q-value data frame (n trials x k action channels). A new row is added to the dataframe every trial
# inputs:   Q_df = current Q-value data frame. Stores q-values related to all action channels until the current trial
#			Q_support_params: mainly for the updated Q_support_params.reward_value and Q_support_params.chosen_action
#			dpmndefaults: To also update the dopamine release parameter dpmn_DAp according to the reward value
# outputs:  Q_df, Q_support_params,dpmndefaults = updated Q-value data
# frame, Q_support_params, dpmndefaults


def helper_update_Q_df(Q_df, Q_support_params, dpmndefaults, trial_num):

    # Required to perform mathematical calculations with data frame values
    Q_support_params = untrace(Q_support_params)
    #Q_df = untrace(Q_df)
    #print('Q_support_params.chosen_action[trial_num]', Q_support_params.chosen_action[trial_num])
    print(
        'Q_support_params.chosen_action[0]',
        Q_support_params.chosen_action[0])
    print('trial_num', trial_num)

    if Q_support_params.chosen_action[0] != 'stop' and Q_support_params.chosen_action[0] != 'none':

        #print('Qdf', Q_df)
        trial_wise_q_df = Q_df.iloc[trial_num]  # trial wise Q data frame
        print('TRIAL WISE Q DF', trial_wise_q_df)
        trial_wise_chosen_action = Q_support_params.chosen_action  # trial wise chosen action

        # Probability of reward value to lie in an uniform distribution
        # (bayes_unif_min, bayes_unif_max)
        u_val = sp_st.uniform.pdf(
            Q_support_params.reward_value,
            Q_support_params.bayes_unif_min,
            Q_support_params.bayes_unif_max)

        # q value of the chosen action
        q_val_chosen = trial_wise_q_df[trial_wise_chosen_action]
        #print('trialwiseqdf', trial_wise_q_df)
        #print('qvalchosen', q_val_chosen)

        # probability of reward value to lie in a normal distribution with (mean =
        # current q-value of the chosen action, variance = bayes_sF)
        n_val = sp_st.norm.pdf(
            Q_support_params.reward_value,
            q_val_chosen,
            Q_support_params.bayes_sF)

        # Calculate the new CPP
        # bayes_CPP = (u_val * Q_support_params.bayes_H) / ((u_val *
        # Q_support_params.bayes_H) + (n_val * (1 - Q_support_params.bayes_H)))

        # error = reward_calue - current q-value
        q_error = Q_support_params.reward_value.values - q_val_chosen.values
        #q_error = Q_support_params.reward_value.values - trial_wise_q_df
        da_inc = Q_support_params.reward_value.values - np.max(trial_wise_q_df)
        #print('Q_support_params.REWARD_VALUE', type(Q_support_params.reward_value))
        #print('Q_support_params type', type(Q_support_params))

        # Update the current q-value accordingly
        q_val_updated = q_val_chosen.values + Q_support_params.q_alpha.values * q_error
        #print('qvalUPDATED', type(q_val_updated))

        # First append an dataframe for the new trial, with q-values copied from
        # the previous trial
        new_data = pd.DataFrame(Q_df[-1:].values, columns=Q_df.columns)
        #print('newdata', new_data)
        Q_df = Q_df.append(new_data)
        #print('newQdf', Q_df)

        # Update the correct value with q_val_updated
        Q_df.iloc[trial_num + 1][trial_wise_chosen_action] = q_val_updated
        #print('Qdf', Q_df)
        #print('Qdf data types', Q_df.dtypes)

        # update dopamine burst ?
        #dpmndefaults.dpmn_DAp = q_error * bayes_CPP * Q_support_params.dpmn_CPP_scale
        #dpmndefaults.dpmn_DAp = q_error * Q_support_params.dpmn_CPP_scale
        dpmndefaults.dpmn_DAp = da_inc * Q_support_params.dpmn_CPP_scale

    else:

        new_data = pd.DataFrame(Q_df[-1:].values, columns=Q_df.columns)
        #print('newdata', new_data)
        Q_df = Q_df.append(new_data)
        #print('newQdf', Q_df)

    return Q_df, Q_support_params, dpmndefaults
