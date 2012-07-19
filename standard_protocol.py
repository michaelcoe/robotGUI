from protocol_entry import ProtocolEntry
  
STANDARD_PROTOCOL = [
  # CMD values of 0x00 - 0x7F(127) are defined here
  # Add CMD definitions 
  # for bootloader (0x00 - 0x1F)

  ProtocolEntry('CMD_NACK', 0x00),       # START_APPLICATION', 0
  ProtocolEntry('CMD_ACK', 0x01),
  ProtocolEntry('CMD_READ_PM', 0x02),
  ProtocolEntry('CMD_WRITE_PM', 0x03),
  ProtocolEntry('CMD_READ_EE', 0x04),
  ProtocolEntry('CMD_WRITE_EE', 0x05),
  ProtocolEntry('CMD_READ_CM', 0x06),
  ProtocolEntry('CMD_WRITE_CM', 0x07),
  ProtocolEntry('CMD_RESET', 0x08),
  ProtocolEntry('CMD_READ_ID', 0x09),
  ProtocolEntry('CMD_READ_GOTO', 0x10),
  
  ProtocolEntry('SET_THRUST', 0x11),
  ProtocolEntry('SET_STEER', 0x12),
  ProtocolEntry('ECHO', 0x1F),      # send back the received packet
  
  # for IMU (0x20 - 0x3F),
  ProtocolEntry('GET_IMU_DATA', 0x20,'l6h'),
  ProtocolEntry('GET_IMU_LOOP', 0x21),
  ProtocolEntry('START_IMU_SAVE', 0x22),
  ProtocolEntry('STOP_IMU_SAVE', 0x23),
  
  ProtocolEntry('SET_POSE_SAVE_FLASH', 0x25),
  ProtocolEntry('SET_ESTIMATE_POSE', 0x26),
  
  ProtocolEntry('TX_SAVED_IMU_DATA', 0x2A),
  ProtocolEntry('TX_SAVED_STATE_DATA', 0x2B, 'l3f'),
  ProtocolEntry('TX_DUTY_CYCLE', 0x2C, 'l3f'),
  
  ProtocolEntry('START_AUTO_CTRL', 0x30),
  ProtocolEntry('STOP_AUTO_CTRL', 0x31),
  
  ProtocolEntry('ERASE_MEM_SECTOR', 0x3A),
  
  ProtocolEntry('RESET_STOPWATCH', 0x3B),
  
  ProtocolEntry('BASE_ECHO', 0x3f),
  
  # CMD values of 0x80(128), - 0xEF(239), are available for user applications.
  ProtocolEntry('SET_THRUST_OPEN_LOOP', 0x80),
  ProtocolEntry('SET_THRUST_CLOSED_LOOP', 0x81),
  ProtocolEntry('SET_PID_GAINS', 0x82, '10h'),
  ProtocolEntry('GET_PID_TELEMETRY', 0x83),
  ProtocolEntry('SET_CTRLD_TURN_RATE', 0x84, '=h'),
  ProtocolEntry('GET_IMU_LOOP_ZGYRO', 0x85, '='+2*'Lhhh'),
  ProtocolEntry('SET_MOVE_QUEUE', 0x86),
  ProtocolEntry('SET_STEERING_GAINS', 0x87, '5h'),
  ProtocolEntry('SOFTWARE_RESET', 0x88),
  ProtocolEntry('SPECIAL_TELEMETRY', 0x89, '=LL'+14*'h'),
  ProtocolEntry('ERASE_SECTORS', 0x8A),
  ProtocolEntry('FLASH_READBACK', 0x8B)
  # CMD values of 0xF0(240) - 0xFF(255) are reserved for future use
]
