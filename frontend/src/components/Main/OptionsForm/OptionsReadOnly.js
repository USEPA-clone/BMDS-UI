import PropTypes from "prop-types";
import React from "react";

import {getLabel} from "@/common";
import {checkOrEmpty} from "@/common";
import {
    MODEL_CONTINUOUS,
    MODEL_DICHOTOMOUS,
    MODEL_MULTI_TUMOR,
    MODEL_NESTED_DICHOTOMOUS,
} from "@/constants/mainConstants";
import {
    continuousBmrOptions,
    dichotomousBmrOptions,
    distTypeOptions,
    litterSpecificCovariateOptions,
} from "@/constants/optionsConstants";
import {ff} from "@/utils/formatters";

const OptionsReadOnly = props => {
    const {options, modelType, idx} = props;
    return (
        <tr>
            <td>{idx + 1}</td>
            {modelType === MODEL_CONTINUOUS ? (
                <>
                    <td>{getLabel(options.bmr_type, continuousBmrOptions)}</td>
                    <td>{ff(options.bmr_value)}</td>
                    <td>{ff(options.tail_probability)}</td>
                    <td>{ff(options.confidence_level * 100)}%</td>
                    <td>{getLabel(options.dist_type, distTypeOptions)}</td>
                </>
            ) : null}
            {modelType === MODEL_DICHOTOMOUS || modelType === MODEL_MULTI_TUMOR ? (
                <>
                    <td>{getLabel(options.bmr_type, dichotomousBmrOptions)}</td>
                    <td>{ff(options.bmr_value)}</td>
                    <td>{ff(options.confidence_level * 100)}%</td>
                </>
            ) : null}
            {modelType === MODEL_NESTED_DICHOTOMOUS ? (
                <>
                    <td>{getLabel(options.bmr_type, dichotomousBmrOptions)}</td>
                    <td>{ff(options.bmr_value)}</td>
                    <td>{ff(options.confidence_level * 100)}%</td>
                    <td>
                        {getLabel(
                            options.litter_specific_covariate,
                            litterSpecificCovariateOptions
                        )}
                    </td>
                    <td>{checkOrEmpty(options.estimate_background)}</td>
                    <td>{options.bootstrap_iterations}</td>
                    <td>{options.bootstrap_seed}</td>
                </>
            ) : null}
        </tr>
    );
};
OptionsReadOnly.propTypes = {
    options: PropTypes.object,
    modelType: PropTypes.string.isRequired,
    idx: PropTypes.number,
};
export default OptionsReadOnly;
