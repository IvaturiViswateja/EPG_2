#!/usr/bin/env python3
import sys
sys.path.append('C:\\NSR\\DeepPath_GYM\\scripts')
sys.path.append('C:\\NSR\\learn2learn_project\\learn2learn\\gym\\envs')
sys.path.append('C:\\NSR\\learn2learn_project\\learn2learn\\algorithms\\epg')


import random
import gym
import numpy as np
# from gym.envs import KG_env
from gym.error import DependencyNotInstalled
from gym.envs.KG_env import Knowledgegraph_gym
from meta_env import MetaEnv
from utils import *

dataPath = 'C:\\NSR\\NELL-995\\'

class Meta_KG(MetaEnv,Knowledgegraph_gym):
    def __init__(self, task_meta = None):
        Knowledgegraph_gym.__init__(self,dataPath)
        MetaEnv.__init__(self, task_meta)

    # -------- MetaEnv Methods --------
    def set_task(self, task):
        MetaEnv.set_task(self, task)
        self.goal_relation = task['relation']

    def sample_tasks(self,num_tasks):
        relation_idx  = np.random.choice(np.arange(0,401,1, dtype=int), (num_tasks,))
        relations = self.relations[relation_idx]
        tasks = [{'relation': relation} for relation in relations]
        return tasks
    
  ##-------------GYM methods------------  	
    def reset(self, *args, **kwargs):
        Knowledgegraph_gym.reset(self, *args, **kwargs)
        return self._get_obs()
	
    def step(self, action):
        assert self.action_space.contains(action), f"{action!r} ({type(action)}) invalid"
        assert self.state is not None, "Call reset before using step method."
        terminated = 0 # Whether the episode has finished
        curr_pos, target_pos = 0,self.state
        chosed_relation = self.relations[action]
        choices = []
        for line in self.kb:
            triple = line.rsplit()
            e1_idx = self.entity2id_[triple[0]]
            if curr_pos == e1_idx and triple[2] == chosed_relation and triple[1] in self.entity2id_:
                choices.append(triple)
        if len(choices) == 0:
            reward = -1
            self.die += 1
            self.state = (curr_pos, target_pos, self.die) # stay in the initial state
            return np.array(self.state,dtype=np.float32),reward, terminated, False, {}
        else: # find a valid step
            path = random.choice(choices)
            self.path.append(path[2] + ' -> ' + path[1])
            self.path_relations.append(path[2])
            # print('Find a valid step', path)
            # print('Action index', action)
            self.die = 0
            new_pos = self.entity2id_[path[1]]
            reward = 0
            self.state = (new_pos, target_pos, self.die)
            if new_pos == target_pos:
                print('Find a path:', self.path)
                terminated = 1
                reward = 1
                self.state = None
            return np.array(self.state,dtype=np.float32),reward, terminated, False, {}

    def get_valid_actions(self, entityID):
        actions = set()
        for line in self.kb:
            triple = line.split()
            e1_idx = self.entity2id_[triple[0]]
            if e1_idx == entityID:
                actions.add(self.relation2id_[triple[2]])
        return np.array(list(actions))

    def path_embedding(self, path):
        embeddings = [self.relation2vec[self.relation2id_[relation],:] for relation in path]
        embeddings = np.reshape(embeddings, (-1,embedding_dim))
        path_encoding = np.sum(embeddings, axis=0)
        return np.reshape(path_encoding,(-1, embedding_dim))

if __name__ == '__main__':
    env = KG_task_env()
    for task in [env.get_task(), env.sample_tasks(1)[0]]:
        env.set_task(task)
        env.reset()
        action = env.action_space.sample()
        env.step(action)
