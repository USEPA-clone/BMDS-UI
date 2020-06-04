import React from "react";

const InputForm = props => {
    return (
        <tr>
            {Object.keys(props.row).map((key, index) => {
                return [
                    <td key={index}>
                        <input
                            type="number"
                            className="form-control"
                            name={key}
                            value={props.row[key]}
                            onChange={e => props.onChange(e, props.dataset_id, props.idx)}
                        />
                    </td>,
                ];
            })}
            <td>
                <button
                    className="btn btn-danger"
                    style={{float: "right"}}
                    onClick={e => props.delete(e, props.dataset_id, props.idx)}>
                    <i className="fa fa-trash"></i>
                </button>
            </td>
        </tr>
    );
};
export default InputForm;
