import numpy as np
import xml.etree.ElementTree as ET
from hand_imitation.env.environments.base import MujocoEnv

from hand_imitation.env.models import TableArena
from hand_imitation.env.models.base import MujocoXML
from hand_imitation.env.utils.mjcf_utils import xml_path_completion, array_to_string, find_elements
from hand_imitation.env.utils.random import np_random
from hand_imitation.env.models.objects import YCB_SIZE, YCB_ORIENTATION
import transforms3d
import random
import trimesh
import os
import sys

class SHAPENETPCRelocate(MujocoEnv):
    def __init__(self, has_renderer, render_gpu_device_id=-1, category='mug', 
                    object_name="0001", object_scale=1, random_object=True, 
                    randomness_scale=1, obj_poses=None, large_force=False, 
                    unseen_obj=False, num_pc=100, rotate_pc=False, density=1000, **kwargs):
        self.np_random = None
        self.seed()
        self.category = category
        self.object_name = object_name
        self.object_scale = object_scale
        self.randomness_scale = randomness_scale
        self.large_force = large_force
        self.unseen_obj = unseen_obj
        self.num_pc = num_pc
        self.rotate_pc = rotate_pc
        self.density = density
        #############################################
        #############################################
        #############################################
        self.num_act=18
        #############################################
        #############################################
        #############################################

        self.num_category = {'bottle':75, 'can':75, 'remote':63, 'mug':58, 'camera': 78}

        self.__additional_kwargs = kwargs
        if obj_poses is not None:
            self.obj_poses = np.load(obj_poses, allow_pickle=True).item()
        else:
            self.obj_poses = None
       

        self.object_names = []
        if unseen_obj is False:
            for idx in range(40):
                if idx < 10:
                    self.object_names.append('000'+str(idx))
                else:
                    self.object_names.append('00'+str(idx))
       
        else:
            for idx in range(40, self.num_category[category]):
                self.object_names.append('00'+str(idx))


        self.random_object = random_object
        super().__init__(has_renderer=has_renderer, has_offscreen_renderer=False, render_camera=None,
                         render_gpu_device_id=render_gpu_device_id, control_freq=100, horizon=200, ignore_done=True,
                         hard_reset=True)

        # Setup action range
        self.act_mid = np.mean(self.mjpy_model.actuator_ctrlrange, axis=1)
        self.act_rng = 0.5 * (self.mjpy_model.actuator_ctrlrange[:, 1] - self.mjpy_model.actuator_ctrlrange[:, 0])
        #self.target_robot_pos=target_robot_pos


    def _pre_action(self, action, policy_step=False):
        action = np.clip(action, -1.0, 1.0)
        action = self.act_mid + action * self.act_rng  # mean center and scale
        self.sim.data.ctrl[:] = action

    def _reset_internal(self):
        super()._reset_internal()
        self.sim.forward()
        self.sim.set_state(self.sim_state_initial)
        self.sim.forward()
        # self.sim.data.qpos[30] = self.np_random.uniform(low=0.15, high=0.15) * self.randomness_scale - 0.1
        # self.sim.data.qpos[31] = self.np_random.uniform(low=-0.15, high=0.15) * self.randomness_scale
        ##############################################################################################################
        ##############################################################################################################
        ##############################################################################################################
        self.sim.data.qpos[self.num_act] = self.np_random.uniform(low=0.15, high=0.15) * self.randomness_scale - 0.1
        self.sim.data.qpos[self.num_act+1] = self.np_random.uniform(low=-0.15, high=0.15) * self.randomness_scale
        ##############################################################################################################
        ##############################################################################################################
        ##############################################################################################################
        self.mjpy_model.body_pos[self.target_object_bid, 0] = self.np_random.uniform(low=-0.30, high=0.10)
        self.mjpy_model.body_pos[self.target_object_bid, 1] = self.np_random.uniform(low=-0.15, high=0.15)
        self.mjpy_model.body_pos[self.target_object_bid, 2] = self.np_random.uniform(low=0.15, high=0.25)

        if self.obj_poses is not None:
            if self.object_name in self.obj_poses:
                obj_init = random.choice(self.obj_poses[self.object_name])
            else:
                obj_init = random.choice(self.obj_poses[random.choice(list(self.obj_poses.keys()))])

            state = self.sim.get_state()
            state[1][-7:] = obj_init
            self.sim.forward()
            self.sim.set_state(state)
            self.sim.forward()
                

    def _get_observations(self):
        qp = self.data.qpos.ravel()
        obj_pos = self.data.body_xpos[self.obj_bid].ravel()
        palm_pos = self.data.site_xpos[self.S_grasp_sid].ravel()
        target_pos = self.data.body_xpos[self.target_object_bid].ravel()
        # original_obs =  np.concatenate([qp[:30], palm_pos - obj_pos, palm_pos - target_pos, obj_pos - target_pos])
        ########################################################################################################################
        ########################################################################################################################
        ########################################################################################################################
        original_obs =  np.concatenate([qp[:self.num_act], palm_pos - obj_pos, palm_pos - target_pos, obj_pos - target_pos])
        ########################################################################################################################
        ########################################################################################################################
        ########################################################################################################################

        quat = self.sim.get_state()[1][-4:]
        r = transforms3d.quaternions.quat2mat(quat)
        # t = self.sim.get_state()[1][30:33]
        ##############################################################
        ##############################################################
        ##############################################################
        t = self.sim.get_state()[1][self.num_act:self.num_act+3]
        ##############################################################
        ##############################################################
        ##############################################################
       
        bbox_now = (np.matmul(self.bbox_original, r[:3,:3].T) + t).ravel()

        #random_idx = np.random.choice(self.pointcloud_original.shape[0], self.num_pc)
        #sampled_pointcloud_original = self.pointcloud_original[random_idx, :]
        # set not rotating pc as the only option
        #return np.concatenate([original_obs, quat, bbox_now, self.sampled_pointcloud])
        # print(f"len of original_obs={len(original_obs)}")
        # print(f"len of quat={len(quat)}")
        # print(f"len of bbox_now={len(bbox_now)}")
        # print(f"len of quat={len([float(self.object_name)])}")
        return np.concatenate([original_obs, quat, bbox_now, [float(self.object_name)]])

    def set_target_robot_pos(self,target_robot_pos):
        self.target_robot_pos=target_robot_pos
    
    def set_target_hand_joints(self,target_hand_joints,obj_pose):
        self.target_hand_joints=target_hand_joints
        self.initial_obj_pose=obj_pose
    
    def get_traj(self,obj_pose_path,hand_joints_path):
        self.obj_pose_seq=np.load(obj_pose_path,allow_pickle=True)
        self.hand_joints_seq=np.load(hand_joints_path,allow_pickle=True)
    
    def reward(self, action):
        obj_pos = self.data.body_xpos[self.obj_bid].ravel()
        palm_pos = self.data.site_xpos[self.S_grasp_sid].ravel()
        target_pos = self.data.body_xpos[self.target_object_bid].ravel()
        is_contact = self.check_contact(self.body_geom_names, self.robot_geom_names)
        
        reward = -0.1 * np.linalg.norm(palm_pos - obj_pos)  # take hand to object
        if is_contact:
            reward += 0.1
            lift = max(min(obj_pos[2], target_pos[2]) - YCB_SIZE['mug'][2] / 2.0, 0)
            reward += 50 * lift
            if lift > 0.015:  # if object off the table
                obj_target_distance = np.linalg.norm(obj_pos - target_pos)
                reward += 2.0  # bonus for lifting the object
                reward += -0.5 * np.linalg.norm(palm_pos - target_pos)  # make hand go to target
                reward += -1.5 * obj_target_distance  # make object go to target

                if obj_target_distance < 0.1:
                    reward += 1 / (obj_target_distance + 0.01) 
        
        return reward

    def _setup_references(self):
        self.target_object_bid = self.sim.model.body_name2id("target")
        self.S_grasp_sid = self.sim.model.site_name2id('S_grasp')
        self.obj_bid = self.sim.model.body_name2id(self.object_body_name)

    def _load_model(self):
        arena = TableArena(table_full_size=(1.2, 1.2, 0.05), table_friction=(1, 0.5, 0.01), table_offset=(0, 0, 1.0),
                           bottom_pos=(0, 0, -1), has_legs=True)
        #################################################################################
        #################################################################################
        #################################################################################
        # xml_file = xml_path_completion("adroit/adroit_relocate.xml")
        xml_file = xml_path_completion("inspire/urdf/handright9253.xml")
        #################################################################################
        #################################################################################
        #################################################################################

        robot = MujocoXML(xml_file)
        mesh_list = find_elements(robot.worldbody[0], tags="geom", return_first=False)
        robot_geom_names = [geom.get("name", "") for geom in mesh_list]
        self.robot_geom_names = [name for name in robot_geom_names if len(name) > 0]

        # Add YCB Object for relocation task
        object_size = YCB_SIZE['mug']

        # Parse args for YCB object geom
        additional_kwargs = self.__additional_kwargs.copy()
        for key, value in additional_kwargs.items():
            if isinstance(value, (np.ndarray, tuple, list, float, int)):
                additional_kwargs[key] = array_to_string(value)
        if "condim" not in additional_kwargs:
            additional_kwargs["condim"] = "4"
        if "margin" not in additional_kwargs:
            additional_kwargs["margin"] = "0.003"

        # Add ycb object into the arena and cache its body name
        # randomly get an object
        if self.random_object:
            self.object_name = random.choice(self.object_names)
        #print(f'current dir: {os.getcwd()}, {sys.path[-1]}')
        try:
            self.obj = trimesh.load(f'hand_imitation/hand_imitation/env/models/assets/shapenet_{self.category}/visual/{self.object_name}/model_transform_scaled.obj') 
        except:
            self.obj = trimesh.load(f'{sys.path[-1]}/hand_imitation/hand_imitation/env/models/assets/shapenet_{self.category}/visual/{self.object_name}/model_transform_scaled.obj')
        self.bbox_original = self.obj.bounding_box.bounds.copy()
        
        self.pointcloud_original = np.asarray(self.obj.vertices) * self.object_scale
        random_idx = np.random.choice(self.pointcloud_original.shape[0], self.num_pc)
        self.sampled_pointcloud = self.pointcloud_original[random_idx, :].ravel()


        arena.add_shapenet_object(self.category, self.object_name, pos=[0, 0, object_size[2] / 2], quat=YCB_ORIENTATION['mug'],
                             free=True, density=self.density, idn=0, scale=self.object_scale, **additional_kwargs)
        self.object_body_name = arena.objects[0].body_name
        object_geom = find_elements(arena.objects[0].body, "geom", return_first=False)
        self.body_geom_names = [geom.get("name", "") for geom in object_geom if
                                geom.get("name", "").startswith("collision")]



        # Reduce actuator force if not large force
        if not self.large_force:
            for actuator in find_elements(robot.actuator, 'general', return_first=False):
                if 'A_ARR' in actuator.get('name'):
                    actuator.set('gainprm', '300 0 0 0 0 0 0 0 0 0')
            #print(f'Limit actuator force to 250')



        # Add target visualization for relocation task
        target_position = np.array(object_size) / 2 + np.array([0.05, 0.05, 0.12])
        object_target = ET.Element("body", name="target", pos=array_to_string(target_position),
                                   quat=array_to_string(YCB_ORIENTATION['mug']))
        target_geom = ET.Element("geom", type="mesh", mesh=f"{self.object_name}_visual_mesh", contype="0",
                                 conaffinity="0", rgba="0 1 0 0.125")
        object_target.append(target_geom)
        arena.worldbody.append(object_target)

        # Merge robot xml with table arena
        robot.merge(arena, merge_body="default")
        self.model = robot
        self.model.save_model("relocate_temp.xml")

    def seed(self, seed=None):
        self.np_random, seed = np_random(seed)
        return [seed]

    @property
    def action_spec(self):
        high = np.ones_like(self.mjpy_model.actuator_ctrlrange[:, 1])
        low = -1.0 * np.ones_like(self.mjpy_model.actuator_ctrlrange[:, 0])
        return low, high

    def set_state(self, qpos, qvel):
        import mujoco_py
        assert qpos.shape == (self.mjpy_model.nq,) and qvel.shape == (self.mjpy_model.nv,)

        old_state = self.sim.get_state()
        new_state = mujoco_py.MjSimState(old_state.time, qpos, qvel, old_state.act, old_state.udd_state)
        self.sim.set_state(new_state)
        self.sim.forward()

    def get_env_state(self):
        """
        Get state of hand as well as objects and targets in the scene
        """
        qp = self.sim.data.qpos.ravel().copy()
        qv = self.sim.data.qvel.ravel().copy()
        # hand_qpos = qp[:30]
        ######################################################
        ######################################################
        ######################################################
        hand_qpos = qp[:self.num_act]
        ######################################################
        ######################################################
        ######################################################
        obj_pos = self.sim.data.body_xpos[self.obj_bid].ravel()
        palm_pos = self.sim.data.site_xpos[self.S_grasp_sid].ravel()
        target_pos = self.sim.data.site_xpos[self.target_object_bid].ravel()
        return dict(hand_qpos=hand_qpos, obj_pos=obj_pos, target_pos=target_pos, palm_pos=palm_pos, qpos=qp, qvel=qv)

    def set_env_state(self, state_dict):
        """
        Set the state which includes hand as well as objects and targets in the scene
        """
        qp = state_dict['qpos']
        qv = state_dict['qvel']
        obj_pos = state_dict['obj_pos']
        target_pos = state_dict['target_pos']
        self.set_state(qp, qv)
        self.mjpy_model.body_pos[self.obj_bid] = obj_pos
        self.mjpy_model.site_pos[self.target_object_bid] = target_pos
        self.sim.forward()

    @property
    def spec(self):
        this_spec = Spec(self._get_observations().shape[0], self.action_spec[0].shape[0])
        return this_spec

    def set_seed(self, seed=None):
        return self.seed(seed)


class Spec:
    def __init__(self, observation_dim, action_dim):
        self.observation_dim = observation_dim
        self.action_dim = action_dim
