import csv, time, argparse
import subprocess
import os
from pathlib import Path

from email_sender import send_email_with_attachment
from arguments_parser import parser
from output_utils import (
    csv_path,
    ensure_output_dir,
    get_output_dir,
    report_path,
    topo_disc_path,
)


def run_topology_discovery(controller_ip, controller_port, controller_name, rest_port, target_length, query_interval, consec_failures, iface, nolinks, env):
    if nolinks:
        cmd = ['python3', 'topology_discovery.py', '-ip', controller_ip, '-p', str(controller_port), '-n', controller_name, '-r', rest_port, '-l', str(target_length), '-q', str(query_interval), '-c', str(consec_failures), '-if', iface, '-k']
    else:
        cmd = ['python3', 'topology_discovery.py', '-ip', controller_ip, '-p', str(controller_port), '-n', controller_name, '-r', rest_port, '-l', str(target_length), '-q', str(query_interval), '-c', str(consec_failures), '-if', iface]
    print(cmd)
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)


def run_workload_simulation(controller_ip, controller_port, topology_type, topology_parameters, env):
    if topology_type == 'leaf-spine':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', str(controller_port), '-t', topology_type, '--num-leafs', f'{topology_parameters[0]}', '--num-spines', f'{topology_parameters[1]}']
        print(cmd)
    elif topology_type == 'mesh':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', str(controller_port), '-t', topology_type, '--num-switches', f'{topology_parameters}']
        print(cmd)
    elif topology_type == '3-tier':
        cmd = ['python3', 'workload.py', '-ip', controller_ip, '-p', str(controller_port), '-t', topology_type, '--num-cores', f'{topology_parameters[0]}', '--num-aggs', f'{topology_parameters[1]}', '--num-access', f'{topology_parameters[2]}']
        print(cmd)
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, env=env)


def write_to_csv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['num_nodes', 'avg_tdt', 'avg_ldt', 'avg_total', 'avg_lldp_len', 'avg_pkt_len', 'avg_lldp_count', 'avg_pkt_count', 'avg_cpu', 'avg_memory'])
        writer.writerows(data)


def report(filename, args, run_data):
    report_text = ''
    for arg in vars(args):
        if getattr(args, arg) is not None:
            report_text += (f'{arg}: {getattr(args, arg)}\n')
    for lines in run_data:
        report_text += str(lines) + '\n'
    with open(filename, 'w', newline='') as f:
        f.write(report_text)


def get_target(topo, size, type='sep'):
    if topo == 'mesh':
        return size
    elif topo == 'leaf-spine':
        if type == 'sep':
            return size, size * 2
        else:
            return (size + size * 2)
    elif topo == '3-tier':
        if type == 'sep':
            return size, size, size
        else:
            return (size + size + size)


def generate_plots(output_dir: Path):
    try:
        from plot_results import plot_csv
        written = plot_csv(csv_path(output_dir), outdir=output_dir)
        print(f'Gráficos gerados em {output_dir}: {len(written)} arquivo(s)')
    except Exception as exc:
        print(f'Aviso: não foi possível gerar gráficos ({exc})')


if __name__ == '__main__':
    args = parser('topology-script')
    output_dir = ensure_output_dir(get_output_dir(args.controller_name, args.topology))
    avg_file = csv_path(output_dir)
    report_file = report_path(output_dir)
    topo_disc_file = topo_disc_path(output_dir)

    env = os.environ.copy()
    env['SDNBM_OUTPUT_DIR'] = str(output_dir)

    print(f'Saída do teste: {output_dir}')

    data = []
    running_data = []
    running = True
    i = args.start
    while running and (get_target(args.topology, i, 'agg') < args.maxsize):
        ldt_sum, tdt_sum, lldp_sum, lldp_sum_count, pkt_sum, pkt_sum_count, count_cpu, count_mem = 0, 0, 0, 0, 0, 0, 0, 0
        target_length = get_target(args.topology, i, 'agg')
        disc_stats, link_stats, pkt_stats = [], [], []
        print('Running for topo_length = {}'.format(target_length))
        for j in range(0, args.trials):
            print('running topology.py')
            topology_proc = run_topology_discovery(
                args.controller_ip, args.controller_port, args.controller_name, args.rest_port,
                get_target(args.topology, i, 'agg'), args.query_interval, args.consec_failures,
                args.iface, args.no_links, env,
            )
            print('running workload.py')
            run_simulation_proc = run_workload_simulation(
                args.controller_ip, args.controller_port, args.topology,
                get_target(args.topology, i, 'sep'), env,
            )
            topology_proc.wait()
            print('finished topology.py')

            run_simulation_proc.stdin.flush()
            run_simulation_proc.communicate()
            run_simulation_proc.wait()
            print('finished workload.py')

            with open(topo_disc_file, 'r') as f:
                lines = f.readlines()
                last_line = lines[-1].strip()
                values = last_line.split(",")
                if len(values) > 1:
                    topology_discovery_time, total_discovery_time, total_lldp, count_lldp, total_pkt, count_pkt, avg_cpu, avg_memory = float(values[0]), float(values[1]), float(values[2]), float(values[3]), float(values[4]), float(values[5]), float(values[6]), float(values[7])
                    link_discovery_time = total_discovery_time - topology_discovery_time
                else:
                    topology_discovery_time = -1.0

                if topology_discovery_time != -1.0:
                    disc_stats.append(topology_discovery_time)
                    pkt_stats.append([total_lldp, count_lldp, total_pkt, count_pkt])
                    link_stats.append(link_discovery_time)
                    print(disc_stats)
                    tdt_sum += total_discovery_time
                    ldt_sum += link_discovery_time
                    lldp_sum += total_lldp
                    lldp_sum_count += count_lldp
                    pkt_sum += total_pkt
                    pkt_sum_count += count_pkt
                    count_cpu += avg_cpu
                    count_mem += avg_memory
                else:
                    running = False
                    break

        avg_tdt, avg_ldt, avg_lldp, avg_lldp_count, avg_pkt, avg_pkt_count, avg_cpu_final, avg_mem = (
            tdt_sum / args.trials, ldt_sum / args.trials, lldp_sum / args.trials,
            lldp_sum_count / args.trials, pkt_sum / args.trials, pkt_sum_count / args.trials,
            count_cpu / args.trials, count_mem / args.trials,
        )
        data.append([target_length, avg_tdt, avg_ldt, (avg_tdt + avg_ldt), avg_lldp, avg_pkt, avg_lldp_count, avg_pkt_count, avg_cpu_final, avg_mem])
        running_data.append([target_length, disc_stats, link_stats, pkt_stats])
        print(data)
        i = i + args.diff

        write_to_csv(avg_file, data)
        report(report_file, args, running_data)

    generate_plots(output_dir)

    if os.environ.get("SDNBM_SEND_EMAIL", "").strip() == "1":
        send_email_with_attachment(
            f'({args.controller_name}) Task completed',
            'Experiment finished successfully',
            [str(avg_file), str(report_file)],
        )
