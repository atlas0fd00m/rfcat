from .const_gollum import RfUtils

class Tools:
    """
    General tools for Gollum CC1111.
    """

    @classmethod
    def get_minimum_rx_filter_bandwidth(cls, freq: int, data_rate: int) -> int:
        """
        Calculate the minimum Rx filter bandwidth for a given frequency and data rate value.

        :param freq: Frequency
        :param data_rate: Data rate
        :return: Minimum filter bandwidth
        """

        freq_uncertainty = 20e-6 * freq * 2
        min_bw = data_rate + freq_uncertainty

        for bw_val in RfUtils.RX_FILTER_BANDWIDTH_VALUES:
            if bw_val > min_bw:
                return bw_val

if __name__ == '__main__':
    pass
