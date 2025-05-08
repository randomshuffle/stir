from ldt_params import LDTParameters
from stir import run_STIR
from math import log2, ceil, floor, log

common_params = {
    'secparam': 128,
    'hashsize': 256,
    'field_size_bits': 192,
}

# Initial code parameters
horizontal_code_params = {
    'rate_bits': 3,
    'dist': 1 - 2**(-3),
}
vertical_code_params = {
    'rate_bits': 1,
    'dist': 0.5,
}

tensor_params = {
    'log_k': 30,
    'rate_bits': horizontal_code_params['rate_bits'] + vertical_code_params['rate_bits'],
    'dist': horizontal_code_params['dist'] * vertical_code_params['dist'],
    'num_col_checks': ceil(common_params['secparam'] / horizontal_code_params['rate_bits']), 
    'num_row_checks': None,
    'log_horizontal_k': None,
    'log_vertical_k': None,
}
tensor_params['num_row_checks'] = 1 # ceil(1 / horizontal_code_params['dist'])
tensor_params['log_horizontal_k'] = ceil((tensor_params['log_k'] + log2(tensor_params['num_col_checks'])) / 2)
tensor_params['log_vertical_k'] = tensor_params['log_k'] - tensor_params['log_horizontal_k']

# Final code parameters, should just be Reed Solomon
final_code_params = {
    'log_k': tensor_params['log_horizontal_k'],
    'rate_bits': None,
    'dist': None,
}
final_code_params['rate_bits'] = tensor_params['log_k'] + tensor_params['rate_bits'] - final_code_params['log_k']
final_code_params['dist'] = 1 - 2**(-final_code_params['rate_bits'])


sumcheck1_params = {
    'log_k': tensor_params['log_horizontal_k'],
    'degree': 3,
}
sumcheck2_params = {
    'log_k': tensor_params['log_horizontal_k'],
    'degree': 2,
}

codeswitch_params = {
    'log_k': tensor_params['log_horizontal_k'],
    'rate_bits': horizontal_code_params['rate_bits'],
}

batching_params = {
    'log_k': tensor_params['log_horizontal_k'],
    'num_batch': 3,
    'rate_bits': final_code_params['rate_bits'],
    'batch_loss_bits': final_code_params['rate_bits'] - 2, # this is assuming we have good batching for rs codes in list decoding
}

stir_params_common = {
    'pow': 0,
    'stopping_condition': 2**10,
    'conj': 1,
    'fold': 16,
    'max_len_ratio': 2,
}

stir_params1 = {
    'log_k': tensor_params['log_horizontal_k'],
    'rate_bits': final_code_params['rate_bits'],
}

stir_params2 = {
    'log_k': tensor_params['log_k'],
    'rate_bits': tensor_params['rate_bits'],
}

def proof_size(message_size, rate_bits, hash_size, queries):
    print(f"Message size: {message_size}, Rate bits: {rate_bits}, Hash size: {hash_size}, Queries: {queries}")
    return (message_size + rate_bits) * queries * hash_size

if __name__ == '__main__':

    queries_to_w_for_lit_reduction = tensor_params['num_col_checks'] * tensor_params['num_row_checks']
    queries_to_wprime_for_lit_reduction = tensor_params['num_col_checks']
    x1 = proof_size(tensor_params['log_k'], tensor_params['rate_bits'], common_params['hashsize'], queries_to_w_for_lit_reduction)
    x2 = proof_size(tensor_params['log_horizontal_k'], horizontal_code_params['rate_bits'], common_params['hashsize'], queries_to_wprime_for_lit_reduction)
    print("LIT reduction argument size:")
    print(x1)
    print(x2)

    sumcheck_field_elements = sumcheck1_params['degree'] * sumcheck1_params['log_k'] + sumcheck2_params['degree'] * sumcheck2_params['log_k']
    x3 = sumcheck_field_elements * common_params['field_size_bits']
    print("Sumcheck argument size:")
    print(x3)

    # queries_codeswitch = ceil(common_params['secparam'] / codeswitch_params['rate_bits'])
    # x4 = proof_size(codeswitch_params['log_k'], codeswitch_params['rate_bits'], common_params['hashsize'], queries_codeswitch)
    # print("Codeswitch argument size:")
    # print(x4)
    
    queries_batching = ceil(batching_params['num_batch'] * common_params['secparam'] / batching_params['batch_loss_bits'])
    x5 = proof_size(batching_params['log_k'], batching_params['rate_bits'], common_params['hashsize'], queries_batching)
    print("Batching argument size:")
    print(x5)

    ldt_params1 = LDTParameters(
        secparam=common_params['secparam'],
        hashsize=common_params['hashsize'],
        pow=stir_params_common['pow'],
        log_degree=stir_params1['log_k'],
        field_size_bits=common_params['field_size_bits'],
        rho_bits=stir_params1['rate_bits'],
        conj=stir_params_common['conj']
    )
    sum_stir1 = run_STIR(
        ldt_params1,
        fold=[stir_params_common['fold']],
        max_len_ratio=[stir_params_common['max_len_ratio']],
        stopping_condition=stir_params_common['stopping_condition']
    )
    x6 = sum_stir1.argument_size()
    print("STIR argument size:")
    print(x6)

    print("Total new argument size:")
    print(x1 + x2 + x3 + 0 + x5 + x6)

    print("\nVS\n")

    ldt_params2 = LDTParameters(
        secparam=common_params['secparam'],
        hashsize=common_params['hashsize'],
        pow=stir_params_common['pow'],
        log_degree=stir_params2['log_k'],
        field_size_bits=common_params['field_size_bits'],
        rho_bits=stir_params2['rate_bits'],
        conj=stir_params_common['conj']
    )
    sum_stir2 = run_STIR(
        ldt_params2,
        fold=[stir_params_common['fold']],
        max_len_ratio=[stir_params_common['max_len_ratio']],
        stopping_condition=stir_params_common['stopping_condition']
    )
    print("Original STIR argument size:")
    print(sum_stir2.argument_size())

    print("Ratio of new to old argument size:")
    print((x1 + x2 + x3 + 0 + x5 + x6) / sum_stir2.argument_size())