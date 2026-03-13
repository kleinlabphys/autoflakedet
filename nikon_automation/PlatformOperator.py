import time
from PriorControl import PriorControl

class PlatformOperator(PriorControl):

    def get_stage_xy(self):
            _, xy_pos_str = self.send_prior_cmd("controller.stage.position.get")
            return map(int, xy_pos_str.split(','))
        
    def get_stage_x(self):
        return self.get_stage_xy()[0]
    
    def get_stage_y(self):
        return self.get_stage_xy()[1]
    
    def get_stage_z(self):
        _, z_pos_str = self.send_prior_cmd("controller.z.position.get")
        z = int(z_pos_str)
        return z
    
    def get_stage_xyz(self):
        x, y = self.get_stage_xy()
        z = self.get_stage_z()
        return (x, y, z)

    # Not ideal but does the job for a synchronous program
    def wait_for_platform(self, targetPosition):
        maximum_wait_cycles = 20
        cycle_wait_time = 0.5

        cycle_iterations = 0
        while cycle_iterations < maximum_wait_cycles:
            xy_status, _ = self.send_prior_cmd("controller.stage.busy.get", expected_status=[0, 1, 2, 3])
            z_status, _ = self.send_prior_cmd("controller.z.busy.get", expected_status=[0, 4])
            moving_status = xy_status or z_status
            if moving_status or targetPosition != self.get_stage_xyz():
                time.sleep(cycle_wait_time)
            else:
                return
            
            cycle_iterations += 1

    def synch_go_to_xyz(self, targetPosition):
        self.send_prior_cmd(f"controller.stage.goto-position {targetPosition[0]} {targetPosition[1]}")
        self.send_prior_cmd(f"controller.z.goto-position {targetPosition[2]}")
        self.wait_for_platform(targetPosition)
    
