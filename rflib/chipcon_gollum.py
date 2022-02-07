#!/usr/bin/env ipython
import struct
from typing import Optional
from . import RfCat

from rflib.ccspecan import SPECAN_QUEUE

from .utils_gollum import Tools

from .chipcon_usb import ChipconUsbTimeoutException, keystop
from .chipcondefs import RFST_SIDLE
from .const import MOD_ASK_OOK, SYNCM_CARRIER, USB_RX_WAIT
from .const_gollum import *

# PandwaRF/PandwaRF Rogue specific methods
class PandwaRF(RfCat):

    def __init__(self, idx=0, debug=False, copyDongle=None, RfMode=RFST_SIDLE, safemode=False):
        super().__init__(idx, debug, copyDongle, RfMode, safemode)
        self.endec = None
        self._initPandwaRf()

    def recv(self, app, cmd=None, wait=USB_RX_WAIT):
        # Override recv to replace some commands (e.g specan)
        if app == APP_SPECAN:
            if cmd == SPECAN_QUEUE:
                cmd = CMD_SPECAN_QUEUE

        r, t = super().recv(app, cmd, wait)
        return r, t

    # RECV / SEND COMMANDS (Low Level)

    # APP_SYSTEM_GOLLUM

    def _sendAppSystemGollum(self, cmd: int):
        return self.send(APP_SYSTEM_GOLLUM, cmd, b'')

    def _sendGetFwVersion(self):
        return self._sendAppSystemGollum(CMD_GET_FW_VERSION)

    def _sendGetSerialNumber(self):
        return self._sendAppSystemGollum(CMD_DEVICE_SERIAL_NUMBER_GOLLUM)
        
    # APP_NIC

    def _sendAppNic(self, cmd: int, payload: bytes):
        return self.send(APP_NIC, cmd, payload)
    
    def _recvAppNic(self, cmd: int, wait=USB_RX_WAIT):
        return self.recv(APP_NIC, cmd, wait)
    
    def _sendEncodingMode(self, compressionMode: bool):
        _data = struct.pack("B", compressionMode)
        return self._sendAppNic(CMD_NIC_ENCODING_MODE, _data)
    
    def _sendRecvInfiniteMode(self, rxInfiniteMode: bool):
        _data = struct.pack("B", rxInfiniteMode)
        return self._sendAppNic(CMD_NIC_RECV_INFINITE_MODE, _data)
    
    def _recv(self):
        return self._recvAppNic(CMD_NIC_RECV)
    
    def _recvRle(self):
        return self._recvAppNic(CMD_NIC_RECV_RLE)
    
    def _sendRequestRemainingData(self):
        return self._sendAppNic(CMD_NIC_ENCODING_MODE, b"")
    
    def _recvRemainingData(self):
        return self._recvAppNic(CMD_NIC_RECV_REMAINING_DATA)
    
    def _recvRemainingDataRle(self):
        return self._recvAppNic(CMD_NIC_RECV_REMAINING_DATA_RLE)
    
    def _sendXmitInfiniteMode(self, enqueueMode: bool, expectedBlockSize: int):
        _data = struct.pack("<BH", enqueueMode, expectedBlockSize)
        return self._sendAppNic(CMD_NIC_RECV_INFINITE_MODE, _data)
    
    def _sendXmit(self, dataLength: int, repeat: int, offset: int, data: bytes):
        _data = struct.pack("<HHH", dataLength, repeat, offset) + data
        return self._sendAppNic(CMD_NIC_XMIT, _data)
    
    def _sendXmitRle(self, dataLength: int, repeat: int, offset: int, data: bytes):
        _data = struct.pack("<HHH", dataLength, repeat, offset) + data
        return self._sendAppNic(CMD_NIC_XMIT, _data)
    
    def _sendStartDatarateDetection(self, occurenceThreshold: int):
        _data = struct.pack('B', occurenceThreshold)
        return self._sendAppNic(CMD_NIC_START_DATARATE_DETECTION, _data)
    
    def _sendStopDatarateDetection(self):
        return self._sendAppNic(CMD_NIC_STOP_DATARATE_DETECTION, b"")
    
    def _recvDatarateDetected(self, wait=USB_DATARATE_MEAS_WAIT_MS):
        return self._recvAppNic(CMD_NIC_DATARATE_DETECTED, wait)
    
    def _recvDatarateDetectedEnd(self, wait=USB_DATARATE_MEAS_WAIT_MS):
        return self._recvAppNic(CMD_NIC_DATARATE_DETECTED_END, wait)
    
    def _sendRecvAsyncMode(self, asyncMode: bool):
        _data = struct.pack("B", asyncMode)
        return self._sendAppNic(CMD_NIC_RECV_ASYNC_MODE, _data)
    
    def _sendRecvAsyncProcessingEnabled(self, asyncProcessingMode: bool):
        _data = struct.pack("B", asyncProcessingMode)
        return self._sendAppNic(CMD_NIC_RECV_ASYNC_PROCESSING_ENABLED, _data)
    
    def _recvAsyncDataNordic(self):
        pass
    
    def _recvAsyncDataCC1111(self):
        pass
    
    # APP_SPECAN

    def _sendAppSpecan(self, cmd: int, payload: bytes):
        return self.send(APP_SPECAN, cmd, payload)
    
    def _recvAppSpecan(self, cmd: int):
        return self.recv(APP_SPECAN, cmd)

    def _sendRfcatStartSpecan(self, numberOfChannels: int):
        _data = struct.pack("B", numberOfChannels)
        return self._sendAppSpecan(CMD_RFCAT_START_SPECAN, _data)

    def _sendRfcatStopSpecan(self):
        return self._sendAppSpecan(CMD_RFCAT_STOP_SPECAN, b"")

    def _sendSpecanPktDelay(self, delay: int):
        _data = struct.pack("B", delay)
        return self._sendAppSpecan(CMD_SPECAN_PKT_DELAY, _data)

    def _recvSpecanQueue(self):
        return self._recvAppSpecan(CMD_SPECAN_QUEUE)

    # APP_FREQFINDER

    def _sendAppFreqfinder(self, cmd: int, payload: bytes):
        return self.send(APP_FREQFINDER, cmd, payload)
    
    def _recvAppFreqfinder(self, cmd: int):
        return self.recv(APP_FREQFINDER, cmd)

    def _sendFreqfinderStart(self):
        return self._sendAppFreqfinder(CMD_FREQFINDER_START, b"")

    def _recvFreqfinderResult(self):
        return self._recvAppFreqfinder(CMD_FREQFINDER_RESULT)

    def _sendFreqfinderStop(self):
        return self._sendAppFreqfinder(CMD_FREQFINDER_STOP, b"")

    # APP_RF

    def _sendAppRf(self, cmd: int, payload: bytes):
        return self.send(APP_RF, cmd, payload)
    
    def _recvAppRf(self, cmd: int, timeout: int = USB_RX_WAIT):
        return self.recv(APP_RF, cmd, timeout)

    def _sendRfSendConfig(self,
                           frequency: int,
                           modulation: int,
                           deviation: int,
                           datarate: int,
                           packetLength: int):
        _data = struct.pack('<IBIIB', frequency, modulation, deviation, datarate, packetLength)
        return self._sendAppRf(CMD_RF_SEND_CONFIG, _data)

    def _sendRfTransmitData(self, size: int, repeat: int, offset: int, data: bytes):
        _data = struct.pack('<BBB', size, repeat, offset) + data
        return self._sendAppRf(CMD_RF_TRANSMIT_DATA, _data)

    def _sendRfSetFreq(self, frequency: int):
        _data = struct.pack("<I", frequency)
        return self._sendAppRf(CMD_RF_SET_FREQ, _data)

    def _sendRfSetPower(self, invert: bool, pset: bool, power: int):
        _data = struct.pack("BBB", invert, pset, power)
        return self._sendAppRf(CMD_RF_SET_POWER, _data)

    def _sendRfSetModulation(self, invert: bool, modulation: int):
        _data = struct.pack("BB", invert, modulation)
        return self._sendAppRf(CMD_RF_SET_MODULATION, _data)

    def _sendRfSetDatarate(self, datarate: int):
        _data = struct.pack("<I", datarate)
        return self._sendAppRf(CMD_RF_SET_DATARATE, _data)

    def _sendRfSetMaxPower(self, invert: bool):
        _data = struct.pack("B", invert)
        return self._sendAppRf(CMD_RF_SET_MAXPOWER, _data)

    def _sendRfSetRxFilterBw(self, bandwidth: int):
        _data = struct.pack("<I", bandwidth)
        return self._sendAppRf(CMD_RF_SET_RXFILTERBW, _data)

    def _sendRfSetPacketFlen(self, packetLength: int):
        _data = struct.pack("B", packetLength)
        return self._sendAppRf(CMD_RF_SET_PACKETFLEN, _data)

    def _sendRfSetSyncmode(self, syncMode: int):
        _data = struct.pack("B", syncMode)
        return self._sendAppRf(CMD_RF_SET_SYNCMODE, _data)

    def _sendRfSetPktCrc(self, crcMode: bool):
        _data = struct.pack("B", crcMode)
        return self._sendAppRf(CMD_RF_SET_PKTCRC, _data)

    def _sendRfSetChanSpc(self, channelSpacing: int):
        _data = struct.pack("B", channelSpacing)
        return self._sendAppRf(CMD_RF_SET_CHANSPC, _data)

    def _sendRfStartJamming(self,
                             startFrequency: int,
                             datarate: int,
                             modulation: int,
                             stopFrequency: int):
        _data = struct.pack("<IIBI", startFrequency, datarate, modulation, stopFrequency)
        return self._sendAppRf(CMD_RF_START_JAMMING, _data)

    def _sendRfStopJamming(self):
        return self._sendAppRf(CMD_RF_STOP_JAMMING, b"")

    def _sendRfBruteForceSetup(self,
                                delay: int,
                                encoderSymbol0: int,
                                encoderSymbol1: int,
                                encoderSymbol2: int,
                                encoderSymbol3: int):
        _data = struct.pack("BBBBB", delay, encoderSymbol0, encoderSymbol1, encoderSymbol2, encoderSymbol3)
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_SETUP, _data)
    
    def _sendRfBruteForceSetupFunction(self,
                                        functionSize: int,
                                        functionMask: int,
                                        functionValue: int):
        _data = struct.pack("B", functionSize)
        _data += int.to_bytes(functionMask, functionSize, 'big')
        _data += int.to_bytes(functionValue, functionSize, 'big')
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_SETUP_FUNCTION, _data)

    def _sendRfBruteForceStart(self,
                                codeLength: int,
                                startValue: int,
                                stopValue: int,
                                frameRepeat: int,
                                littleEndian: bool,
                                delay: int,
                                encoderSymbol0: int,
                                encoderSymbol1: int,
                                encoderSymbol2: int,
                                encoderSymbol3: int,
                                syncWordSize: int,
                                syncWord: int):
        _data = struct.pack("<BIIBBBBBBBB", codeLength, startValue, stopValue, frameRepeat, littleEndian, delay, encoderSymbol0, encoderSymbol1, encoderSymbol2, encoderSymbol3, syncWordSize)
        _data += int.to_bytes(syncWord, syncWordSize, 'little')
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_START, _data)

    def _sendRfBruteForceStop(self):
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_STOP, b"")

    def _recvRfBruteForceStatusUpdate(self, timeout=USB_BRUTEFORCE_STATUS_WAIT_MS):
        return self._recvAppRf(CMD_RF_BRUTE_FORCE_STATUS_UPDATE, timeout)

    def _sendRfSetTxRxPowerAmpMode(self, amplifierAction: int):
        _data = struct.pack("B", amplifierAction)
        return self._sendAppRf(CMD_RF_SET_TXRX_POWER_AMP_MODE, _data)

    def _sendRfGetTxRxPowerAmpMode(self):
        return self._sendAppRf(CMD_RF_SET_TXRX_POWER_AMP_MODE, b"")

    def _sendRfSetRxModeAuto(self):
        return self._sendAppRf(CMD_RF_SET_RX_MODE_AUTO, b"")

    def _sendRfStopAll(self):
        return self._sendAppRf(CMD_RF_STOP_ALL, b"")

    # Utils functions

    def _getFirmwareVersion(self) -> bytes:
        r, t = self._sendGetFwVersion()
        return r

    def _getSerialNumber(self) -> bytes:
        r, t = self._sendGetSerialNumber()
        return r

    def _initPandwaRf(self) -> None:
        self.setAmpMode(RF_POWER_AMPLIFIERS_ACTION_ALL_OFF)


    # Overloading functions

    def getPartNum(self) -> int:
        return 0x11

    def reprHardwareConfig(self):
        output= []
        hardware = self.getBuildInfo()
        output.append("Dongle:              %s" % hardware.split(b' ')[0])

        fwVersion = self._getFirmwareVersion()
        output.append("Firmware rev:        %s" % fwVersion)

        # see if we have a bootloader by loooking for it's recognition semaphores
        # in SFR I2SCLKF0 & I2SCLKF1
        if(self.peek(0xDF46,1) == b'\xF0' and self.peek(0xDF47,1) == b'\x0D'):
            output.append("Bootloader:          CC-Bootloader")
        elif(self.peek(0xDF46,1) == b'\xCC' and self.peek(0xDF47,1) == b'\x01'):
            output.append("Bootloader:          Gollum CCTL v1")
        elif(self.peek(0xDF46,1) == b'\xCC' and self.peek(0xDF47,1) == b'\x02'):
            output.append("Bootloader:          GollumCCTL v2")
        elif(b"CCtl" in hardware):
            output.append("Bootloader:          Gollum CCTL")
        else:
            output.append("Bootloader:          Not installed")
        return "\n".join(output)

    def reprRadioConfig(self) -> str:
        output = []
        output.append(super().reprRadioConfig())

        output.append("\n== PandwaRF Specific ==")
        output.append(f"Amplification Mode:  {self.reprAmpMode()}")

        return '\n'.join(output)


    # User functions
    
    def setFreq(self, freq: int) -> None:
        """
        Modify carrier's frequency.

        :param freq: New frequency
        :return:
        """
        if type(freq) is float:
            freq = int(freq) # Because the specan calls setFreq with a float
        self._sendRfSetFreq(freq)

    def setPower(self, power: int, pset: bool = True, invert: bool = False) -> None:
        """
        Modify output power.

        :param power: New output power
        :param pset: If false, OOK modulation is used, the logic 0 and logic 1 power levels shall be 
         programmed to index 0 and 1 respectively, i.e. PA_TABLE0 and PA_TABLE1.
        :param invert: Invert parameter for power
        :return:
        """
        self._sendRfSetPower(invert, pset, power)

    def setMdmModulation(self, modulation: int, invert: bool = False) -> None:
        """
        Modify modulation format.

        :param modulation: Modulation type
        :param invert: Invert parameter for modulation
        :return:
        """
        self._sendRfSetModulation(invert, modulation)

    def setMdmDRate(self, datarate: int) -> None:
        """
        Modify data rate.

        :param datarate: New data rate
        :return:
        """
        self._sendRfSetDatarate(datarate)

    def setMaxPower(self, invert: bool = False) -> None:
        """
        Set power to max.

        :param invert: Invert parameter
        :return:
        """
        self._sendRfSetMaxPower(invert)

    def setRxFilterBw(self, bandwidth: int) -> None:
        """
        Modify RX filter bandwidth.

        :param bandwidth: New RX filter bandwidth
        :return:
        """
        self._sendRfSetRxFilterBw(bandwidth)

    def makePktFLEN(self, packetLength: int) -> None:
        """
        Modify packet length.
        
        :param packetLength: New packet length
        :return:
        """
        self._sendRfSetPacketFlen(packetLength)

    def setMdmSyncMode(self, syncMode: int) -> None:
        """
        Modify sync mode.

        :param syncMode: New sync mode
        :return:
        """
        self._sendRfSetSyncmode(syncMode)


    def setEnablePktCRC(self, crcMode: bool) -> None:
        """
        Modify packet CRC state.
        
        :param crcMode: New packet CRC state
        :return:
        """
        self._sendRfSetPktCrc(crcMode)

    def setMdmChanSpc(self, channelSpacing: int) -> None:
        """
        Modify channel spacing.

        :param channelSpacing: New channel spacing
        :return:
        """
        if type(channelSpacing) is float:
            channelSpacing = int(channelSpacing) # Because the specan calls setFreq with a float
        self._sendRfSetChanSpc(channelSpacing)

    def stopAllRf(self) -> None:
        """
        Stop all RF activity by setting Mac state Idle directly.
        """
        self._sendRfStopAll()

    def getAmpMode(self) -> bytes:
        '''
        get the amplifier mode (RF amp external to CC1111)
        '''
        r, t = self._sendRfGetTxRxPowerAmpMode()
        return r

    def reprAmpMode(self) -> str:
        ampMode = int.from_bytes(self.getAmpMode(), 'little')
        if ampMode == RF_POWER_AMPLIFIERS_ACTION_ALL_OFF:
            return "Amplifiers OFF"
        elif ampMode == RF_TX_POWER_AMPLIFIER_ACTION_ON:
            return "TX Amplifier only"
        elif ampMode == RF_RX_POWER_AMPLIFIER_ACTION_ON:
            return "RX Amplifier only"
        elif ampMode == RF_TX_RX_POWER_AMPLIFIER_ACTION_ON:
            return "TX & RX Amplifiers ON"
        elif ampMode == RF_TX_POWER_AMPLIFIER_ACTION_ON_TX:
            return "TX Amplifier only when transmitting"
        elif ampMode == RF_RX_POWER_AMPLIFIER_ACTION_ON_RX:
            return "RX Amplifier only when receiving"
        elif ampMode == RF_TX_RX_POWER_AMPLIFIER_ACTION_ON_TX_RX:
            return "TX & RX Amplifiers only when transmitting & receiving"
        elif ampMode == RF_ANT_POWER_ENABLE:
            return "Antenna power enabled"
        elif ampMode == RF_ANT_POWER_DISABLE:
            return "Antenna power disabled"
        else:
            return "Unknown amplification mode"

    def rxSetup(self, 
                frequency: int,
                modulation: int,
                datarate: int,
                packetLength: int = 200,
                filterBandwidth: int = 0) -> None:
        """
        Initial configuration for Rx.

        :param frequency: Frequency
        :param modulation: Modulation
        :param datarate: Data rate
        :param packetLength: Packet length
        :param filterBandwidth: Rx filter bandwidth
        :return:
        """

        self.setMdmModulation(modulation)
        self.setFreq(frequency)
        self.setMdmDRate(datarate)
        self.setMdmSyncMode(RfUtils.SYNC_MODE_NO_PRE_CS)

        # This command writes to the register PKTCTRL1, setting to zero APPEND_STATUS and ADR_CHK
        self.setPktPQT(0)
        self.makePktFLEN(packetLength)
        # This command writes to the register PKTCTRL0, setting to zero PKT_FORMAT, CRC_EN and LENGTH_CONFIG
        self.setEnablePktDataWhitening(False)
        # This command writes to the register MDMCFG1, setting to zero NUM_PREAMBLE and CHANSPC_E
        self.setEnableMdmFEC(False)
        self.setEnablePktCRC(False)

        if not filterBandwidth:
            filterBandwidth = Tools.get_minimum_rx_filter_bandwidth(frequency, datarate)

        self.setRxFilterBw(filterBandwidth)

    def txSetup(self, 
                frequency: int,
                modulation: int,
                datarate: int,) -> None:
        """
        Initial configuration for Tx.

        :param frequency: Frequency
        :param modulation: Modulation
        :param datarate: Data rate
        :return:
        """

        self.setMdmModulation(modulation)
        self.setFreq(frequency)
        self.setMdmDRate(datarate)
        self.setMaxPower()

    def configSpecan(self, freq: int, channel_spacing: int, rx_bandwidth) -> None:
        """
        Initial configure before starting SpecAn.

        :param freq: Frequency
        :param channel_spacing: Space between channels
        :param rx_bandwidth: Rx Bandwidth
        :return:
        """

        self.setFreq(freq)
        self.setMdmChanSpc(channel_spacing)
        self.setRxFilterBw(rx_bandwidth)

    def doFreqFinder(self) -> Optional[int]:
        self._sendFreqfinderStart()
        freq = None
        print("Waiting for signal....")
        print("(press Enter to stop)")
        while not keystop() and not freq:
            try:
                r, t = self._recvFreqfinderResult()
                freq = int.from_bytes(r, 'little')
            except:
                pass
        return freq

    def RFxmitRle(self, data: bytes, repeat: int, offset: int) -> None:
        """
        Transmit frame (RLE encoded).
        
        :param data: Data to transmit
        :param repeat: Times to repeat
        :param offset: Offset
        :return:
        """
        dataLength = len(data)
        self._sendXmitRle(dataLength, repeat, offset, data)

    def setAmpMode(self, amplifierMode: int = 0) -> None:
        '''
        set the amplifier mode (RF amp external to CC1111)
        0x00    turn off amplifiers
        0x01    turn on TX amplifier only
        0x02    turn on RX amplifier only
        0x05    turn on TX & RX amplifiers (not supported by rev. E)
        0x06    turn on TX amplifier only when transmitting
        0x07    turn on RX amplifier only when receiving
        0x08    turn on TX & RX amplifiers only when transmitting & receiving
        0x03    enable antenna power
        0x04    disable antenna power
        '''
        self._sendRfSetTxRxPowerAmpMode(amplifierMode)

    def doDataRateDetect(self, freq: int, modulation: int, deviation: int = 0, occurenceThreshold=DATARATE_MEAS_OCC_THRESHOLD_DEFAULT):
        '''
        starts the Data rate measurement procedure. Frequency needs to be setup first.
        '''
        print("Entering data rate measurement mode...  measured data rates arriving will be displayed on the screen")
        print("(press Enter to stop)")

        self.setFreq(freq)
        self.setMdmModulation(modulation)
        if deviation > 0:
            self.setMdmDeviatn(deviation)
        self.setMdmDRate(100000)
        self.setMdmSyncMode(SYNCM_CARRIER)
        self.setPktPQT(0)
        self.makePktFLEN(250)
        self.setEnablePktDataWhitening(0)
        self.setEnableMdmFEC(0)
        self.setEnablePktCRC(False)
        self.setMdmChanBW(125000)
        self.setAmpMode(RF_POWER_AMPLIFIERS_ACTION_ALL_OFF)
        self._sendStartDatarateDetection(occurenceThreshold)

        while not keystop():
            # check for SYS_CMD_NIC_DATARATE_DETECTED
            try:
                (y, t) = self._recvDatarateDetected()
                dr, = struct.unpack("<L", y)
                print("(%5.3f) Data rate received: %d bits/s" % (t, dr))

            except ChipconUsbTimeoutException:
                pass

            # check for SYS_CMD_NIC_DATARATE_DETECTED_END
            try:
                y, t = self._recvDatarateDetectedEnd()
                print("(%5.3f) Data rate measurement ended" % t)
                break

            except ChipconUsbTimeoutException:
                pass

        self._sendStopDatarateDetection()        

    def doJamming(self, startFrequency: int, dataRate: int, stopFrequency: int = None) -> None:
        """
        Performs a jamming, either around one frequency (startFrequency) or 
        between 2 frequencies (startFrequency and stopFrequency)

        :param startFrequency: Center Frequency to Jam or start frequency if stopFrequency is set
        :type startFrequency: int
        :param dataRate: Datarate is equivalent to "Spectrum Wideness" here: More datarate => wider is the jamming spectrum
        :type dataRate: int
        :param stopFrequency: Stop frequency, defaults to -1
        :type stopFrequency: int, optional
        """
        print("Entering RF jamming mode...")
        if not stopFrequency:
            stopFrequency = startFrequency

        self._sendRfStartJamming(startFrequency, dataRate, MOD_ASK_OOK, stopFrequency)

        input("press Enter to stop")

        self._sendRfStopJamming()

    def doBruteForceLegacy(self):
        pass
    


class PandwaRFRogue(PandwaRF):

    # RECV / SEND COMMANDS (Low Level)

    # APP_RF

    def _sendRfBruteForceSetupLongSymbol(self,
                                          delay: int,
                                          symbolLength: int,
                                          encSymbol0: int,
                                          encSymbol1: int,
                                          encSymbol2: int,
                                          encSymbol3: int):
        _data = struct.pack("BB", delay, symbolLength)
        endianess = 'big'
        _data += int.to_bytes(encSymbol0, symbolLength, endianess)
        _data += int.to_bytes(encSymbol1, symbolLength, endianess)
        _data += int.to_bytes(encSymbol2, symbolLength, endianess)
        _data += int.to_bytes(encSymbol3, symbolLength, endianess)
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_SETUP_LONG_SYMBOL, _data)

    def _sendRfBruteForceStartSyncCodeTail(self,
                                            syncWordSize: int,
                                            tailWordSize: int,
                                            codeLength: int,
                                            startValue: int,
                                            stopValue: int,
                                            frameRepeat: int,
                                            littleEndian: bool,
                                            syncWord: int,
                                            tailWord: int):
        _data = struct.pack("<BBBIIBB", syncWordSize, tailWordSize, codeLength, startValue, stopValue, frameRepeat, littleEndian)
        _data += int.to_bytes(syncWord, syncWordSize, 'big')
        _data += int.to_bytes(tailWord, tailWordSize, 'big')
        return self._sendAppRf(CMD_RF_BRUTE_FORCE_START_SYNC_CODE_TAIL, _data)


    # User functions

    def doBruteForce(self, 
                     frequency: int, 
                     modulation: int, 
                     datarate: int, 
                     startValue: int,
                     stopValue: int, 
                     codeLength: int, 
                     repeat: int, 
                     delay: int, 
                     encSymbol0: int, 
                     encSymbol1: int, 
                     encSymbol2: int, 
                     encSymbol3: int, 
                     syncWordSize: int, 
                     syncWord: int, 
                     tailWordSize: int, 
                     tailWord: int, 
                     functionSize: int, 
                     functionMask: int, 
                     functionValue: int, 
                     littleEndian=False):
        print("Entering brute force mode...  status arriving will be displayed on the screen")
        print("(press Enter to stop)")

        self.txSetup(frequency, modulation, datarate)
        self._sendRfBruteForceSetupLongSymbol(delay, 3, encSymbol0, encSymbol1, encSymbol2, encSymbol3)
        self._sendRfBruteForceSetupFunction(functionSize, functionMask, functionValue)
        self._sendRfBruteForceStartSyncCodeTail(syncWordSize, tailWordSize, codeLength, startValue, stopValue, repeat, littleEndian, syncWord, tailWord)

        status = 0
        while (not keystop() and (status <= stopValue)):
            # check for SYS_CMD_RF_BRUTE_FORCE_STATUS_UPDATE
            try:
                (y, t) = self._recvRfBruteForceStatusUpdate()
                status, state = struct.unpack("<IB", y)
                if state == STATE_BRUTEFORCE_NOT_STARTED:
                    print("Bruteforce not started yet...")
                elif state == STATE_BRUTEFORCE_ONGOING:
                    print(f"({t}) Brute force status: {status}/{stopValue}")
                elif state == STATE_BRUTEFORCE_FINISHED:
                    print("Bruteforce finished !")
                    break
                else:
                    print("Unknown bruteforce status")

            except ChipconUsbTimeoutException:
                # print "Timeout Brute force status update" 
                pass
            except KeyboardInterrupt:
                print("Please press <enter> to stop")

        self._sendRfBruteForceStop()
