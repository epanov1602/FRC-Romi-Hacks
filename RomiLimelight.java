package frc.robot.sensors;

import frc.robot.Constants;

import edu.wpi.first.networktables.NetworkTable;
import edu.wpi.first.networktables.NetworkTableEntry;
import edu.wpi.first.networktables.NetworkTableInstance;

import java.net.Socket;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.ProtocolException;
import java.net.UnknownHostException;
import java.io.IOException;
 
/**
 * This program demonstrates a simple TCP/IP socket client.
 *
 * @author www.codejava.net
 */ 

public class RomiLimelight {
  public static final int LimelightNTRegistrationPort = 5899;

  protected NetworkTable m_table;
  private NetworkTableEntry m_tx, m_ty, m_ta;

  public double getX() { return m_tx.getDouble(Double.NaN); }
  public double getY() { return m_ty.getDouble(Double.NaN); }
  public double getA() { return m_ta.getDouble(Double.NaN); }

  /** Create a new RomiLimelight. */
  public RomiLimelight() {
    registerForNetworkTables();

    m_table = NetworkTableInstance.getDefault().getTable("limelight");
    m_tx = m_table.getEntry("tx");
    m_ty = m_table.getEntry("ty");
    m_ta = m_table.getEntry("ta");
  }

  /** Register our NetworkTables server with Limelight proxy on the Raspberry Pi */
  private static void registerForNetworkTables() {
    String pi = System.getenv("HALSIMWS_HOST");

    try (Socket socket = new Socket(pi, LimelightNTRegistrationPort)) {
        BufferedReader reader = new BufferedReader(new InputStreamReader(socket.getInputStream()));
        String response = reader.readLine();
        if (response.length() == 1 && response.getBytes()[0] == '0') {
          System.out.println("Registered with Romi Limelight proxy");
          return; // success
        }
        System.err.println(response);
        while ((response = reader.readLine()) != null)
            System.err.println(response);
        throw new java.net.ProtocolException("Failed to setup forwarding on the Pi for Limelight NetworkTables traffic");           
    } catch (UnknownHostException ex) {
        System.err.println("Server not found in RomiLimelight::registerForNetworkTables: " + ex.getMessage()); 
    } catch (IOException ex) {
        System.err.println("I/O error in RomiLimelight::registerForNetworkTables: " + ex.getMessage());
    }
  }
}
