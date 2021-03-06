import numpy as np
import gym
from lake_envs import *
import time
from value_iteration_dp import main as vi_main

"""
Agent is a tabular Q-learner, SARSA learner

Init all q values to random values
terminal state to 0

iterate through states
for each state, pick an action according to epsilon-greedy policy
for bootsrapping, use go off policy and use take the max q value from the next state
(dont choose) an action based on the policy, always do max

Q(s,a) <- Q(s,a) + (learning rate) * (reward + max(Q(s',a')) - Q(s,a))
Above is similar to incremental mean idea. If learning rate was 1 / count, then
it would be same as taking the mean
eventually q values converge

Now just iterate through all states, for each state we have the q values. just
pick the action corresponding to highest q value.

This is the optimal policy (hopefully)


Samething for sarsa, except a' is not argmax, instead it is sampled from
epsilon-greedy policy

"""

def epsilon_greedy(env, state, q_values, eps):

	p = np.random.random()

	if p < eps:
		return env.action_space.sample()
	else:
		# Returns a list, index is the action, value stored is the expected value
		return greedy(state, q_values)


def greedy(state, q_values):

	return np.argmax(q_values[state])

def td_learn(env, num_states, num_actions, SARSA, discount = 0.9):

	"""
	With only 1k episodes, want high exploration in the beginning
	But it should decrease to converge the max values

	Lower bound of learning rate to prevent equaling 0. If equals zero then
	there will be no updates to the q values as experienced

	With specs below, success rate high is ~75% and with a low of ~53%

	"""
	num_episodes = 1000
	eps = 1 # exploration probability
	decay_rate = 0.997 # decay of exploration
	min_learning_rate = 0.001 # lower bound to prevent reaching 0
	default_learning_rate = 0.1 # just in case

	# Table of q values
	# q[state][action] corresponds to total return if action was taken at state
	# and then policy was followed
	q_values = np.zeros((num_states, num_actions))
	q_values_counts = np.zeros((num_states, num_actions))
	

	for i_episode in range(num_episodes):
		state = env.reset()
		while True:
			#env.render()

			action = epsilon_greedy(env, state, q_values, eps)
			current_q_value = q_values[state][action]
			q_values_counts[state][action] += 1
			current_state = state
			learning_rate =  1.0 / q_values_counts[state][action]
			if learning_rate < min_learning_rate:
				learning_rate = min_learning_rate

			state, reward, done, _ = env.step(action)

			# forcing penalization if reached hole
			# bad if we reach back the same position or if its a hole
			# negative reward to distinguish from neutral spots in grid
			if done and reward == 0:
				reward = -1

			# if sarsa, else q learning
			next_state_action = -1
			if SARSA:
				next_state_action = epsilon_greedy(env, state, q_values, eps)
			else:
				next_state_action = greedy(state, q_values)

			q_values[current_state][action] = current_q_value + (learning_rate) * (reward + discount * q_values[state][next_state_action] - current_q_value)
			
			if done:
				# decaying per episode
				eps *= decay_rate
				print ("finished episode {}".format(i_episode + 1))
				break
	return q_values

def policy_extraction(q_values, num_states, num_actions):
	
	policy = [-1 for _ in range(num_states)]

	for state in range(num_states):
		policy[state] = np.argmax(q_values[state])
	return policy

def sample_env(env, policy):

	num_episodes = 100
	avg_reward = 0

	for episode_count in range(num_episodes):
		state = env.reset()
		while True:
			#env.render()
			action = policy[state]

			state, reward, done, _ = env.step(action)

			if done:
				avg_reward = avg_reward + (1.0 / (episode_count + 1)) * (reward - avg_reward)
				break
	return avg_reward

def verify_policy_with_vi(env, policy):

	vi_policy = vi_main(True)
	matching = policy == vi_policy

	q_result = sample_env(env, policy)
	vi_result = sample_env(env, vi_policy)
	print ("result matches with vi {}".format(policy == vi_policy))

	if policy != vi_policy:
		policy = np.reshape(policy, (4,4))
		vi_policy = np.reshape(vi_policy, (4,4))

		print("below is q learning result, with success {}\n".format(q_result))
		print(policy)
		print("below is vi result with sucesss {}\n".format(vi_result))
		print (vi_policy)

def main():

	env_list = ['Deterministic-4x4-FrozenLake-v0', 'Stochastic-4x4-FrozenLake-v0', 'Deterministic-8x8-FrozenLake-v0', 'FrozenLake8x8-v0']
	env_list = [env_list[1]]
	
	# General TD learning
	# Boolean for sarsa method or q learning
	SARSA = False
	for env_item in env_list:
		env = gym.make(env_item)
		num_states = env.observation_space.n
		num_actions = env.action_space.n
		q_values = td_learn(env, num_states, num_actions, SARSA)
		policy = policy_extraction(q_values, num_states, num_actions)
		#verify_policy_with_vi(env, policy)

		print("average reward collected: {}".format(sample_env(env, policy)))
		# uncomment below to for random action
		#sample_env(file, env, V, policy, True)
		env.close()


if __name__ == "__main__":
	main()