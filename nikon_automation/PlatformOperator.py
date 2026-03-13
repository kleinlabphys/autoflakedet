import time
from PriorControl import PriorControl
from utility_fns import wait_until_ready

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
    @wait_until_ready
    def wait_for_platform(self, targetPosition):
        xy_status, _ = self.send_prior_cmd("controller.stage.busy.get", expected_status=[0, 1, 2, 3])
        z_status, _ = self.send_prior_cmd("controller.z.busy.get", expected_status=[0, 4])
        moving_status = xy_status or z_status
        return not (moving_status or targetPosition != self.get_stage_xyz())

    def synch_go_to_xyz(self, targetPosition):
        self.send_prior_cmd(f"controller.stage.goto-position {targetPosition[0]} {targetPosition[1]}")
        self.send_prior_cmd(f"controller.z.goto-position {targetPosition[2]}")
        self.wait_for_platform(targetPosition)
    
